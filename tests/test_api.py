"""
Real HTTP-level tests against the FastAPI app via TestClient, covering the
full auth -> role-gated prediction -> messaging flow, not just isolated
endpoints. Uses a throwaway SQLite file, reset before each test session.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Reset the dev DB file before importing the app, so tests are reproducible
# regardless of what's accumulated from manual local runs.
_db_path = ROOT / "app.db"
if _db_path.exists():
    _db_path.unlink()

fastapi_testclient = pytest.importorskip("fastapi.testclient")
from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

client = TestClient(app)

CARDIO_EXAMPLE = {
    "age": 63, "sex": 1, "cp": 1, "trestbps": 145, "chol": 233,
    "fbs": 1, "restecg": 2, "thalach": 150, "exang": 0,
    "oldpeak": 2.3, "slope": 3, "ca": 0, "thal": 6,
}

BREAST_CANCER_EXAMPLE = {
    "mean_radius": 17.99, "mean_texture": 10.38, "mean_perimeter": 122.8,
    "mean_area": 1001.0, "mean_smoothness": 0.1184, "mean_compactness": 0.2776,
    "mean_concavity": 0.3001, "mean_concave_points": 0.1471, "mean_symmetry": 0.2419,
    "mean_fractal_dimension": 0.07871, "radius_error": 1.095, "texture_error": 0.9053,
    "perimeter_error": 8.589, "area_error": 153.4, "smoothness_error": 0.006399,
    "compactness_error": 0.04904, "concavity_error": 0.05373, "concave_points_error": 0.01587,
    "symmetry_error": 0.03003, "fractal_dimension_error": 0.006193, "worst_radius": 25.38,
    "worst_texture": 17.33, "worst_perimeter": 184.6, "worst_area": 2019.0,
    "worst_smoothness": 0.1622, "worst_compactness": 0.6656, "worst_concavity": 0.7119,
    "worst_concave_points": 0.2654, "worst_symmetry": 0.4601, "worst_fractal_dimension": 0.1189,
}

DIABETES_EXAMPLE = {
    "HighBP": 1, "HighChol": 1, "CholCheck": 1, "BMI": 40, "Smoker": 1, "Stroke": 0,
    "HeartDiseaseorAttack": 0, "PhysActivity": 0, "Fruits": 0, "Veggies": 1,
    "HvyAlcoholConsump": 0, "AnyHealthcare": 1, "NoDocbcCost": 0, "GenHlth": 5,
    "MentHlth": 18, "PhysHlth": 15, "DiffWalk": 1, "Sex": 0, "Age": 9,
    "Education": 4, "Income": 3,
}


@pytest.fixture(scope="module")
def doctor_and_patient_tokens():
    """Registers a real doctor and a real patient assigned to that doctor,
    returns both bearer tokens - the setup every role-gated test builds on."""
    doc_resp = client.post("/auth/register", json={
        "email": "dr.chen@example.com", "password": "supersecret1",
        "full_name": "Dr. Amara Chen", "role": "doctor",
    })
    assert doc_resp.status_code == 200, doc_resp.text
    doctor_token = doc_resp.json()["access_token"]
    doctor_id = doc_resp.json()["user_id"]

    pat_resp = client.post("/auth/register", json={
        "email": "patient.jones@example.com", "password": "supersecret2",
        "full_name": "Sam Jones", "role": "patient", "doctor_id": doctor_id,
    })
    assert pat_resp.status_code == 200, pat_resp.text
    patient_token = pat_resp.json()["access_token"]
    patient_id = pat_resp.json()["user_id"]

    return {
        "doctor_token": doctor_token, "doctor_id": doctor_id,
        "patient_token": patient_token, "patient_id": patient_id,
    }


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_models_endpoint_lists_all_three_diseases():
    resp = client.get("/models")
    assert resp.status_code == 200
    assert set(resp.json().keys()) == {"cardio", "breast_cancer", "diabetes"}


def test_predict_without_auth_is_rejected():
    resp = client.post("/predict/heart", json=CARDIO_EXAMPLE)
    assert resp.status_code == 401


def test_register_rejects_duplicate_email(doctor_and_patient_tokens):
    resp = client.post("/auth/register", json={
        "email": "dr.chen@example.com", "password": "whatever123",
        "full_name": "Someone Else", "role": "doctor",
    })
    assert resp.status_code == 400


def test_register_patient_without_doctor_id_rejected():
    resp = client.post("/auth/register", json={
        "email": "orphan@example.com", "password": "whatever123",
        "full_name": "No Doctor", "role": "patient",
    })
    assert resp.status_code == 400


def test_login_with_wrong_password_rejected(doctor_and_patient_tokens):
    resp = client.post("/auth/login", json={
        "email": "dr.chen@example.com", "password": "wrong-password",
    })
    assert resp.status_code == 401


def test_patient_can_predict_and_it_is_recorded(doctor_and_patient_tokens):
    token = doctor_and_patient_tokens["patient_token"]
    resp = client.post("/predict/heart", json=CARDIO_EXAMPLE, headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert 0.0 <= body["probability"] <= 1.0
    assert "not a medical diagnosis" in body["disclaimer"].lower()

    history = client.get("/predictions/mine", headers=auth_header(token))
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["disease"] == "cardiovascular"


def test_predict_breast_cancer_and_diabetes(doctor_and_patient_tokens):
    token = doctor_and_patient_tokens["patient_token"]
    bc = client.post("/predict/breast-cancer", json=BREAST_CANCER_EXAMPLE, headers=auth_header(token))
    assert bc.status_code == 200
    db_resp = client.post("/predict/diabetes", json=DIABETES_EXAMPLE, headers=auth_header(token))
    assert db_resp.status_code == 200


def test_doctor_can_see_own_patients_predictions(doctor_and_patient_tokens):
    doctor_token = doctor_and_patient_tokens["doctor_token"]
    patient_id = doctor_and_patient_tokens["patient_id"]
    resp = client.get(f"/predictions/patient/{patient_id}", headers=auth_header(doctor_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_doctor_cannot_see_unrelated_patients_predictions(doctor_and_patient_tokens):
    # A second, unrelated doctor should be forbidden from viewing this patient.
    other_doc = client.post("/auth/register", json={
        "email": "dr.other@example.com", "password": "supersecret3",
        "full_name": "Dr. Other", "role": "doctor",
    })
    other_token = other_doc.json()["access_token"]
    patient_id = doctor_and_patient_tokens["patient_id"]
    resp = client.get(f"/predictions/patient/{patient_id}", headers=auth_header(other_token))
    assert resp.status_code == 403


def test_patient_can_message_own_doctor_and_doctor_sees_it(doctor_and_patient_tokens):
    patient_token = doctor_and_patient_tokens["patient_token"]
    doctor_token = doctor_and_patient_tokens["doctor_token"]
    doctor_id = doctor_and_patient_tokens["doctor_id"]
    patient_id = doctor_and_patient_tokens["patient_id"]

    send = client.post(
        "/messages", json={"recipient_id": doctor_id, "body": "I've been feeling dizzy."},
        headers=auth_header(patient_token),
    )
    assert send.status_code == 200
    assert send.json()["body"] == "I've been feeling dizzy."

    thread = client.get(f"/messages/thread/{patient_id}", headers=auth_header(doctor_token))
    assert thread.status_code == 200
    assert len(thread.json()) == 1
    assert thread.json()[0]["sender_name"] == "Sam Jones"


def test_patient_cannot_message_arbitrary_user(doctor_and_patient_tokens):
    patient_token = doctor_and_patient_tokens["patient_token"]
    resp = client.post(
        "/messages", json={"recipient_id": 99999, "body": "hello"},
        headers=auth_header(patient_token),
    )
    assert resp.status_code == 404


def test_non_admin_cannot_list_all_users(doctor_and_patient_tokens):
    resp = client.get("/users", headers=auth_header(doctor_and_patient_tokens["doctor_token"]))
    assert resp.status_code == 403


def test_reports_summary_returns_real_data():
    resp = client.get("/reports/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert "cardio_within_site" in body
    assert len(body["cardio_within_site"]) > 0


def test_password_reset_full_cycle(doctor_and_patient_tokens):
    from api.auth import create_access_token, create_password_reset_token

    email = "dr.chen@example.com"

    # forgot-password returns the same generic message for known and
    # unknown emails (email enumeration protection)
    known = client.post("/auth/forgot-password", json={"email": email})
    unknown = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
    assert known.status_code == 200
    assert known.json() == unknown.json()

    # simulate clicking the emailed link
    token = create_password_reset_token(doctor_and_patient_tokens["doctor_id"])
    reset = client.post("/auth/reset-password", json={"token": token, "new_password": "brandnewpass123"})
    assert reset.status_code == 200

    old_login = client.post("/auth/login", json={"email": email, "password": "supersecret1"})
    assert old_login.status_code == 401

    new_login = client.post("/auth/login", json={"email": email, "password": "brandnewpass123"})
    assert new_login.status_code == 200


def test_access_token_cannot_be_used_as_password_reset_token(doctor_and_patient_tokens):
    resp = client.post("/auth/reset-password", json={
        "token": doctor_and_patient_tokens["doctor_token"], "new_password": "hijacked12345",
    })
    assert resp.status_code == 400
