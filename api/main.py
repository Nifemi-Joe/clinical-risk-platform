"""
Production API serving the three trained models, plus the application
layer: authentication, roles (admin/doctor/patient), prediction history,
and doctor-patient messaging. Loads model artifacts + metadata written by
src/registry/train_production_models.py at startup - this file's ML-serving
half contains NO training logic, only serving logic.

Run with: uvicorn api.main:app --reload
Docs at: http://localhost:8000/docs (FastAPI auto-generates this)
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.auth import create_access_token, create_password_reset_token, get_current_user, hash_password, require_role, verify_password, verify_password_reset_token  # noqa: E402
from api.db import Message, Prediction, Role, User, get_db, init_db  # noqa: E402
from api.email import new_message_notification, password_reset_email  # noqa: E402
from api.reporting import aggregate_contributions, build_methodology, risk_band  # noqa: E402
from api.schemas import (  # noqa: E402
    BreastCancerInput,
    CardioInput,
    Contributor,
    DiabetesInput,
    ForgotPasswordRequest,
    MessageCreate,
    MessageOut,
    PredictionRecord,
    PredictionResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
START_TIME = time.time()

app = FastAPI(
    title="Clinical Risk Prediction API",
    description=(
        "Research prototype estimating disease-risk probabilities from "
        "patient-reported variables. NOT a diagnostic tool - see disclaimer "
        "on every prediction response."
    ),
    version="0.2.0",
)

# Dev-permissive CORS so the Vite dev server (localhost:5173) can call this
# API directly. Tighten to specific origins before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

_REGISTRY: dict[str, dict] = {}


def _load_registry():
    """Load all trained model artifacts + metadata into memory once at
    startup, rather than re-reading from disk on every request."""
    for disease, stem in [
        ("cardio", "cardio_model"),
        ("breast_cancer", "breast_cancer_model"),
        ("diabetes", "diabetes_model"),
    ]:
        model_path = MODELS_DIR / f"{stem}.joblib"
        meta_path = MODELS_DIR / f"{stem}.json"
        if not model_path.exists():
            continue  # allows the API to boot even if one model isn't trained yet
        _REGISTRY[disease] = {
            "pipeline": joblib.load(model_path),
            "metadata": json.loads(meta_path.read_text()),
        }


_load_registry()


def _raw_contributions(pipeline, X_row: pd.DataFrame) -> tuple[list[str], list[float]]:
    """Per-prediction feature contributions on the model's own encoded
    feature space (one entry per one-hot column, not per clinical
    variable — see api/reporting.py for why those get aggregated before
    being shown to a user).

    For linear models (LogisticRegression): exact contribution on the logit
    scale = coefficient * transformed_feature_value - a real, not
    approximated, decomposition for this model family.

    For tree ensembles (RandomForest): SHAP TreeExplainer on this single row
    - slower than the linear case but exact for tree models, computed live
    since caching a background dataset for every request isn't set up in
    this first version (see "what's next" in the technical report).
    """
    preprocessor = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["model"]
    X_t = preprocessor.transform(X_row)
    if hasattr(X_t, "toarray"):
        X_t = X_t.toarray()
    feature_names = [str(f) for f in preprocessor.get_feature_names_out()]

    if hasattr(model, "coef_"):
        contributions = (model.coef_[0] * X_t[0]).tolist()
    else:
        import shap

        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X_t)
        if isinstance(sv, list):
            sv = sv[1]
        elif np.asarray(sv).ndim == 3:
            sv = sv[:, :, 1]
        contributions = np.asarray(sv)[0].tolist()

    return feature_names, [float(c) for c in contributions]


def _top_contributors(feature_names: list[str], contributions: list[float], n: int = 5) -> list[Contributor]:
    """Raw, encoded-feature version — kept for debugging/backward
    compatibility. Prefer feature_contributions (aggregated, translated)
    for anything shown to a person."""
    pairs = sorted(zip(feature_names, contributions), key=lambda p: abs(p[1]), reverse=True)
    return [Contributor(feature=str(f), contribution=round(float(c), 4)) for f, c in pairs[:n]]


def _build_report(
    disease: str, entry: dict, X_row: pd.DataFrame, prob: float, raw_input: dict
) -> dict:
    """Assembles everything api/reporting.py needs into the fields
    PredictionResponse expects: the aggregated human-readable
    contributions, the raw encoded ones (debugging), and the methodology
    summary explaining how this specific number was produced."""
    feature_names, contributions = _raw_contributions(entry["pipeline"], X_row)
    categorical_features = entry["metadata"].get("categorical_features", [])
    feature_contributions = aggregate_contributions(
        disease, feature_names, contributions, categorical_features, raw_input
    )
    methodology = build_methodology(disease, entry["metadata"])
    return {
        "risk_band": risk_band(prob),
        "feature_contributions": [fc.__dict__ for fc in feature_contributions],
        "top_contributors": _top_contributors(feature_names, contributions),
        "methodology": methodology.__dict__,
    }


def _calibration_context(probability: float) -> str:
    """Plain-language framing of what the probability number means - not a
    precise calibration lookup table (that needs the held-out calibration
    curve data wired in, flagged as future work), but avoids presenting a
    bare, easy-to-overtrust number with no context at all."""
    if probability < 0.2:
        return "Model indicates low estimated risk based on the provided variables."
    if probability < 0.5:
        return "Model indicates below-average estimated risk based on the provided variables."
    if probability < 0.8:
        return "Model indicates elevated estimated risk based on the provided variables."
    return "Model indicates high estimated risk based on the provided variables."


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "models_loaded": list(_REGISTRY.keys()),
    }


@app.get("/models")
def list_models():
    return {
        disease: {
            "model": entry["metadata"]["model"],
            "selection_rationale": entry["metadata"]["selection_rationale"],
        }
        for disease, entry in _REGISTRY.items()
    }


@app.get("/models/{disease}")
def model_detail(disease: str):
    if disease not in _REGISTRY:
        raise HTTPException(status_code=404, detail=f"No model loaded for '{disease}'")
    return _REGISTRY[disease]["metadata"]


@app.get("/metrics")
def metrics():
    return {
        disease: {
            k: v for k, v in entry["metadata"].items()
            if "roc_auc" in k or "sensitivity" in k or "specificity" in k
        }
        for disease, entry in _REGISTRY.items()
    }


@app.post("/predict/heart", response_model=PredictionResponse)
def predict_heart(payload: CardioInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if "cardio" not in _REGISTRY:
        raise HTTPException(status_code=503, detail="Cardiovascular model not loaded")
    entry = _REGISTRY["cardio"]
    raw_input = payload.model_dump()
    X_row = pd.DataFrame([raw_input])[entry["metadata"]["feature_columns"]]
    prob = float(entry["pipeline"].predict_proba(X_row)[0, 1])
    _record_prediction(db, user, "cardiovascular", entry["metadata"]["model"], prob, raw_input)
    report = _build_report("cardiovascular", entry, X_row, prob, raw_input)
    return PredictionResponse(
        disease="cardiovascular",
        model=entry["metadata"]["model"],
        probability=round(prob, 4),
        calibration_context=_calibration_context(prob),
        **report,
    )


@app.post("/predict/breast-cancer", response_model=PredictionResponse)
def predict_breast_cancer(payload: BreastCancerInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if "breast_cancer" not in _REGISTRY:
        raise HTTPException(status_code=503, detail="Breast cancer model not loaded")
    entry = _REGISTRY["breast_cancer"]
    # Map underscore field names back to the original UCI feature names
    # ("mean radius", etc.) that the trained pipeline expects.
    data = payload.model_dump()
    renamed = {k.replace("_", " "): v for k, v in data.items()}
    X_row = pd.DataFrame([renamed])[entry["metadata"]["feature_columns"]]
    prob = float(entry["pipeline"].predict_proba(X_row)[0, 1])
    _record_prediction(db, user, "breast_cancer", entry["metadata"]["model"], prob, data)
    report = _build_report("breast_cancer", entry, X_row, prob, renamed)
    return PredictionResponse(
        disease="breast_cancer",
        model=entry["metadata"]["model"],
        probability=round(prob, 4),
        calibration_context=_calibration_context(prob),
        **report,
    )


@app.post("/predict/diabetes", response_model=PredictionResponse)
def predict_diabetes(payload: DiabetesInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if "diabetes" not in _REGISTRY:
        raise HTTPException(status_code=503, detail="Diabetes model not loaded")
    entry = _REGISTRY["diabetes"]
    raw_input = payload.model_dump()
    X_row = pd.DataFrame([raw_input])[entry["metadata"]["feature_columns"]]
    prob = float(entry["pipeline"].predict_proba(X_row)[0, 1])
    _record_prediction(db, user, "diabetes", entry["metadata"]["model"], prob, raw_input)
    report = _build_report("diabetes", entry, X_row, prob, raw_input)
    return PredictionResponse(
        disease="diabetes",
        model=entry["metadata"]["model"],
        probability=round(prob, 4),
        calibration_context=_calibration_context(prob),
        **report,
    )


def _record_prediction(db: Session, user: User, disease: str, model: str, prob: float, input_data: dict):
    db.add(Prediction(
        patient_id=user.id, disease=disease, model_used=model,
        probability=str(round(prob, 4)), input_json=json.dumps(input_data),
    ))
    db.commit()


# ============================================================
# Auth
# ============================================================

@app.post("/auth/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if payload.role not in ("patient", "doctor"):
        raise HTTPException(status_code=400, detail="Self-registration only allowed as 'patient' or 'doctor'")
    if payload.role == "patient" and payload.doctor_id is None:
        raise HTTPException(status_code=400, detail="Patients must specify doctor_id")
    if payload.doctor_id is not None:
        doctor = db.query(User).filter(User.id == payload.doctor_id, User.role == Role.doctor).first()
        if not doctor:
            raise HTTPException(status_code=400, detail="doctor_id does not refer to a valid doctor")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=Role(payload.role),
        doctor_id=payload.doctor_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, role=user.role.value, full_name=user.full_name, user_id=user.id)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, role=user.role.value, full_name=user.full_name, user_id=user.id)


@app.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(
        id=user.id, email=user.email, full_name=user.full_name,
        role=user.role.value, doctor_id=user.doctor_id, is_active=user.is_active,
    )


@app.post("/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Always returns the same generic response whether or not the email
    exists - a real security property (prevents using this endpoint to
    enumerate which emails are registered), not an oversight."""
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        token = create_password_reset_token(user.id)
        reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
        password_reset_email(to=user.email, reset_url=reset_url)
    return {"message": "If that email is registered, a reset link has been sent."}


@app.post("/auth/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user_id = verify_password_reset_token(payload.token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated. You can now sign in with your new password."}


# ============================================================
# Users (admin: manage everyone; doctor: view own patients)
# ============================================================

@app.get("/users", response_model=list[UserOut])
def list_users(user: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        UserOut(id=u.id, email=u.email, full_name=u.full_name, role=u.role.value,
                 doctor_id=u.doctor_id, is_active=u.is_active)
        for u in users
    ]


@app.get("/users/doctors", response_model=list[UserOut])
def list_doctors(db: Session = Depends(get_db)):
    """Public-ish (no auth) so the registration form can populate a doctor
    picker for new patients before they have an account."""
    doctors = db.query(User).filter(User.role == Role.doctor, User.is_active == True).all()  # noqa: E712
    return [
        UserOut(id=d.id, email=d.email, full_name=d.full_name, role=d.role.value,
                 doctor_id=None, is_active=d.is_active)
        for d in doctors
    ]


@app.get("/users/my-patients", response_model=list[UserOut])
def my_patients(user: User = Depends(require_role(Role.doctor)), db: Session = Depends(get_db)):
    patients = db.query(User).filter(User.doctor_id == user.id).all()
    return [
        UserOut(id=p.id, email=p.email, full_name=p.full_name, role=p.role.value,
                 doctor_id=p.doctor_id, is_active=p.is_active)
        for p in patients
    ]


@app.patch("/users/{user_id}/deactivate")
def deactivate_user(user_id: int, admin: User = Depends(require_role(Role.admin)), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.is_active = False
    db.commit()
    return {"status": "deactivated", "user_id": user_id}


# ============================================================
# Prediction history
# ============================================================

@app.get("/predictions/mine", response_model=list[PredictionRecord])
def my_predictions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Prediction).filter(Prediction.patient_id == user.id).order_by(Prediction.created_at.desc()).all()
    return [
        PredictionRecord(id=r.id, patient_id=r.patient_id, disease=r.disease, model_used=r.model_used,
                          probability=float(r.probability), created_at=r.created_at.isoformat())
        for r in rows
    ]


@app.get("/predictions/patient/{patient_id}", response_model=list[PredictionRecord])
def patient_predictions(patient_id: int, user: User = Depends(require_role(Role.doctor, Role.admin)), db: Session = Depends(get_db)):
    if user.role == Role.doctor:
        patient = db.query(User).filter(User.id == patient_id, User.doctor_id == user.id).first()
        if not patient:
            raise HTTPException(status_code=403, detail="Not your patient")
    rows = db.query(Prediction).filter(Prediction.patient_id == patient_id).order_by(Prediction.created_at.desc()).all()
    return [
        PredictionRecord(id=r.id, patient_id=r.patient_id, disease=r.disease, model_used=r.model_used,
                          probability=float(r.probability), created_at=r.created_at.isoformat())
        for r in rows
    ]


# ============================================================
# Messaging (doctor <-> patient, DB-persisted; email is a real
# integration point, logged not delivered in this environment - see
# api/email.py)
# ============================================================

@app.post("/messages", response_model=MessageOut)
def send_message(payload: MessageCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipient = db.query(User).filter(User.id == payload.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    # Only allow messaging within an existing doctor-patient relationship.
    is_valid_pair = (
        (user.role == Role.patient and recipient.id == user.doctor_id)
        or (user.role == Role.doctor and recipient.doctor_id == user.id)
        or user.role == Role.admin
    )
    if not is_valid_pair:
        raise HTTPException(status_code=403, detail="Can only message your assigned doctor/patient")

    msg = Message(sender_id=user.id, recipient_id=recipient.id, body=payload.body)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    new_message_notification(to=recipient.email, sender_name=user.full_name)
    return MessageOut(
        id=msg.id, sender_id=msg.sender_id, sender_name=user.full_name,
        recipient_id=msg.recipient_id, body=msg.body, read=msg.read,
        created_at=msg.created_at.isoformat(),
    )


@app.get("/messages/thread/{other_user_id}", response_model=list[MessageOut])
def get_thread(other_user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Message)
        .filter(
            ((Message.sender_id == user.id) & (Message.recipient_id == other_user_id))
            | ((Message.sender_id == other_user_id) & (Message.recipient_id == user.id))
        )
        .order_by(Message.created_at.asc())
        .all()
    )
    sender_names = {u.id: u.full_name for u in db.query(User).all()}
    return [
        MessageOut(id=m.id, sender_id=m.sender_id, sender_name=sender_names.get(m.sender_id, "Unknown"),
                    recipient_id=m.recipient_id, body=m.body, read=m.read, created_at=m.created_at.isoformat())
        for m in rows
    ]


# ============================================================
# Reports (real data from reports/*.csv, produced by Phases 1-5)
# ============================================================

@app.get("/reports/summary")
def reports_summary():
    """Serves the actual experiment result CSVs as JSON - the same real
    numbers documented in reports/technical-report.md, not re-derived or
    approximated for display."""
    out = {}
    for name, filename in [
        ("cardio_within_site", "cardio_within_site_results.csv"),
        ("cardio_cross_site", "cardio_cross_site_results.csv"),
        ("breast_cancer", "breast_cancer_results.csv"),
        ("diabetes", "diabetes_results.csv"),
    ]:
        path = REPORTS_DIR / filename
        if path.exists():
            out[name] = pd.read_csv(path).to_dict(orient="records")
    return out
