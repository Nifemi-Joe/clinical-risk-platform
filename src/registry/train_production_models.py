"""
Trains and persists ONE production model per disease, to be loaded by the
FastAPI service. Model choice is deliberately NOT always "highest ROC-AUC" -
per the model-selection framework from the original project brief, and per
what Phases 1-5 actually found:

- Cardiovascular: RANDOM FOREST, not logistic regression (which had the
  highest within-site ROC-AUC, 0.961 vs RF's 0.952). Chosen because Phase 1's
  cross-site generalization experiment showed RF holds up better when
  applied to a different hospital's patients (avg cross-site ROC-AUC 0.801
  vs LR's 0.768, and better calibration too) - the realistic deployment
  scenario for a model like this.

- Breast cancer: LOGISTIC REGRESSION (L1), the actual top performer
  (ROC-AUC 0.996) with no countervailing finding against it - simplest
  model, easiest to explain, no reason to pick anything fancier here.

- Diabetes: LOGISTIC REGRESSION with class_weight="balanced", NOT the
  highest-ROC-AUC default XGBoost (0.825). Phase 5 showed the unweighted
  models have unacceptably low sensitivity (as low as 0.5% for default
  Random Forest) - clinically useless for a screening tool despite a
  fine-looking AUC. The balanced logistic regression trades some
  specificity for dramatically better sensitivity (0.770), which is the
  right trade-off for a "don't miss a case" screening context.

Run with: python -m src.registry.train_production_models
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.diseases.breast_cancer.data_loading import load_breast_cancer_df  # noqa: E402
from src.diseases.breast_cancer.schema import NUMERIC_FEATURES as BC_NUM  # noqa: E402
from src.diseases.breast_cancer.schema import TARGET_BINARY as BC_TARGET  # noqa: E402
from src.diseases.cardio.schema import CATEGORICAL_FEATURES as CARDIO_CAT  # noqa: E402
from src.diseases.cardio.schema import NUMERIC_FEATURES as CARDIO_NUM  # noqa: E402
from src.diseases.cardio.schema import TARGET_BINARY as CARDIO_TARGET  # noqa: E402
from src.diseases.diabetes.data_loading import load_diabetes_df  # noqa: E402
from src.diseases.diabetes.schema import CATEGORICAL_FEATURES as DIAB_CAT  # noqa: E402
from src.diseases.diabetes.schema import NUMERIC_FEATURES as DIAB_NUM  # noqa: E402
from src.diseases.diabetes.schema import TARGET_BINARY as DIAB_TARGET  # noqa: E402
from src.pipeline.data_loading import load_site  # noqa: E402
from src.pipeline.preprocessing import build_preprocessor  # noqa: E402

RANDOM_STATE = 42
MODELS_DIR = ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)


def _fit_and_save(pipeline: Pipeline, X, y, name: str, metadata: dict):
    pipeline.fit(X, y)
    joblib.dump(pipeline, MODELS_DIR / f"{name}.joblib")
    (MODELS_DIR / f"{name}.json").write_text(json.dumps(metadata, indent=2))
    print(f"Saved {name}.joblib + {name}.json")


def train_cardio():
    df = load_site("cleveland")
    feature_cols = CARDIO_NUM + CARDIO_CAT
    X, y = df[feature_cols], df[CARDIO_TARGET]
    pipeline = Pipeline(steps=[
        ("preprocess", build_preprocessor(CARDIO_NUM, CARDIO_CAT)),
        ("model", RandomForestClassifier(
            n_estimators=300, max_depth=6, random_state=RANDOM_STATE, n_jobs=-1
        )),
    ])
    metadata = {
        "disease": "cardiovascular",
        "model": "random_forest",
        "selection_rationale": (
            "Chosen over higher within-site-AUC logistic regression (0.961 vs "
            "0.952) because it generalized better cross-site in Phase 1 "
            "(avg ROC-AUC 0.801 vs 0.768, better calibration) - the realistic "
            "deployment scenario."
        ),
        "feature_columns": feature_cols,
        "numeric_features": CARDIO_NUM,
        "categorical_features": CARDIO_CAT,
        "within_site_test_roc_auc": 0.952,
        "avg_cross_site_roc_auc": 0.801,
        "trained_on": "UCI Heart Disease, Cleveland site, full 303 rows",
        "not_a_diagnosis_disclaimer": (
            "Research prototype. Estimates probability from provided "
            "variables. Not a medical diagnosis."
        ),
    }
    _fit_and_save(pipeline, X, y, "cardio_model", metadata)


def train_breast_cancer():
    df = load_breast_cancer_df()
    X, y = df[BC_NUM], df[BC_TARGET]
    pipeline = Pipeline(steps=[
        ("preprocess", build_preprocessor(BC_NUM, [])),
        ("model", LogisticRegression(
            l1_ratio=1, solver="liblinear", max_iter=2000, random_state=RANDOM_STATE
        )),
    ])
    metadata = {
        "disease": "breast_cancer",
        "model": "logistic_regression_l1",
        "selection_rationale": "Top performer (ROC-AUC 0.996), no countervailing finding against it.",
        "feature_columns": BC_NUM,
        "numeric_features": BC_NUM,
        "categorical_features": [],
        "test_roc_auc": 0.996,
        "trained_on": "UCI Wisconsin Diagnostic, full 569 rows",
        "not_a_diagnosis_disclaimer": (
            "Research prototype. Estimates probability from provided "
            "variables. Not a medical diagnosis."
        ),
    }
    _fit_and_save(pipeline, X, y, "breast_cancer_model", metadata)


def train_diabetes():
    df = load_diabetes_df(subsample=True)
    feature_cols = DIAB_NUM + DIAB_CAT
    X, y = df[feature_cols], df[DIAB_TARGET]
    pipeline = Pipeline(steps=[
        ("preprocess", build_preprocessor(DIAB_NUM, DIAB_CAT)),
        ("model", LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE
        )),
    ])
    metadata = {
        "disease": "diabetes",
        "model": "logistic_regression_balanced",
        "selection_rationale": (
            "NOT the highest-AUC model (default XGBoost, 0.825). Chosen because "
            "unweighted models had near-zero sensitivity on this imbalanced "
            "target (default Random Forest: 0.5% sensitivity despite 0.808 "
            "AUC) - clinically useless for a screening tool. Balanced logistic "
            "regression trades specificity for sensitivity 0.770, the right "
            "call for a 'don't miss a case' screening context."
        ),
        "feature_columns": feature_cols,
        "numeric_features": DIAB_NUM,
        "categorical_features": DIAB_CAT,
        "test_roc_auc": 0.820,
        "test_sensitivity": 0.770,
        "test_specificity": 0.716,
        "trained_on": (
            "BRFSS-derived (third-party-cleaned, see SOURCE_diabetes.md), "
            "documented 15,000-row stratified subsample"
        ),
        "not_a_diagnosis_disclaimer": (
            "Research prototype. Estimates probability from provided "
            "variables. Not a medical diagnosis."
        ),
    }
    _fit_and_save(pipeline, X, y, "diabetes_model", metadata)


if __name__ == "__main__":
    train_cardio()
    train_breast_cancer()
    train_diabetes()
