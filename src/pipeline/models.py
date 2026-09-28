"""
Model zoo for the tabular clinical classification task.

Every model is wrapped as preprocessor + estimator in a single sklearn
Pipeline, so that calling .fit(X_train, y_train) inside a CV fold refits
imputation/scaling/encoding on that fold only - no leakage path exists
between models either.

Trimmed from the original full brief per the portfolio-scope decision:
kept everything that's either (a) a meaningful methodological baseline or
(b) commonly used in production tabular ML. Left out of this first pass:
Ridge/LASSO as *separate* entries (covered by LogisticRegression's penalty
param instead, to avoid three near-duplicate linear models cluttering the
comparison table) and CatBoost (adds a third gradient-boosting library for
limited incremental signal over XGBoost + LightGBM at this stage - can be
added back in Phase 3 alongside TabPFN/FT-Transformer if useful).
"""
from __future__ import annotations

from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from src.pipeline.preprocessing import build_preprocessor

try:
    from xgboost import XGBClassifier

    HAS_XGBOOST = True
except ImportError:  # pragma: no cover
    HAS_XGBOOST = False

try:
    from lightgbm import LGBMClassifier

    HAS_LIGHTGBM = True
except ImportError:  # pragma: no cover
    HAS_LIGHTGBM = False


RANDOM_STATE = 42


def _pipeline(estimator, numeric_features=None, categorical_features=None) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor(numeric_features, categorical_features)),
            ("model", estimator),
        ]
    )


def get_model_zoo(numeric_features=None, categorical_features=None) -> dict[str, Pipeline]:
    """Return {model_name: sklearn Pipeline} for every model in scope.

    Disease-agnostic by design: pass the feature lists for whichever disease
    is being run (defaults to the cardiovascular schema for backward
    compatibility with existing call sites). This function, and everything
    it depends on in src/pipeline/, must not change between diseases - only
    the feature lists and data do. That reusability is itself the thing
    being tested in Phase 4."""
    def p(estimator):
        return _pipeline(estimator, numeric_features, categorical_features)

    zoo: dict[str, Pipeline] = {
        "majority_baseline": p(
            DummyClassifier(strategy="most_frequent", random_state=RANDOM_STATE)
        ),
        "logistic_regression": p(
            LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)
        ),
        "logistic_regression_l1": p(
            LogisticRegression(
                l1_ratio=1, solver="liblinear", max_iter=2000, random_state=RANDOM_STATE
            )
        ),
        "decision_tree": p(
            DecisionTreeClassifier(max_depth=5, random_state=RANDOM_STATE)
        ),
        "random_forest": p(
            RandomForestClassifier(
                n_estimators=300, max_depth=6, random_state=RANDOM_STATE, n_jobs=-1
            )
        ),
        "svm_rbf": p(
            # CalibratedClassifierCV(..., ensemble=False) is the
            # forward-compatible replacement for SVC(probability=True),
            # which sklearn began deprecating in 1.9 (removal planned 1.11).
            # Functionally equivalent (Platt scaling under the hood either
            # way) - caught via a real deprecation warning on a
            # newer-sklearn machine, not found in the original build env.
            CalibratedClassifierCV(
                SVC(kernel="rbf", random_state=RANDOM_STATE), ensemble=False
            )
        ),
        "mlp": p(
            MLPClassifier(
                hidden_layer_sizes=(32, 16),
                max_iter=2000,
                random_state=RANDOM_STATE,
                early_stopping=True,
            )
        ),
    }

    if HAS_XGBOOST:
        zoo["xgboost"] = p(
            XGBClassifier(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                eval_metric="logloss",
                random_state=RANDOM_STATE,
            )
        )
    if HAS_LIGHTGBM:
        zoo["lightgbm"] = p(
            LGBMClassifier(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                random_state=RANDOM_STATE,
                verbosity=-1,
            )
        )

    return zoo
