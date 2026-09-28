"""
Hyperparameter search spaces for the tuned models. Kept intentionally small
given the 303-row Cleveland training set - an aggressive search space on this
little data mostly tunes noise, not signal. RandomizedSearchCV inside a
stratified CV loop is used rather than a full nested-CV grid sweep for this
first pipeline pass (nested CV is the documented target for the full
robustness/sensitivity phase, not required to validate the pipeline works).
"""
from __future__ import annotations

SEARCH_SPACES = {
    "logistic_regression": {"model__C": [0.01, 0.1, 1.0, 10.0]},
    "logistic_regression_l1": {"model__C": [0.01, 0.1, 1.0, 10.0]},
    "decision_tree": {"model__max_depth": [2, 3, 4, 5, 6, 8]},
    "random_forest": {
        "model__n_estimators": [100, 300, 500],
        "model__max_depth": [3, 4, 6, 8, None],
    },
    "svm_rbf": {
        "model__estimator__C": [0.1, 1.0, 10.0],
        "model__estimator__gamma": ["scale", "auto"],
    },
    "mlp": {"model__alpha": [0.0001, 0.001, 0.01]},
    "xgboost": {
        "model__n_estimators": [100, 200, 300],
        "model__max_depth": [2, 3, 4],
        "model__learning_rate": [0.02, 0.05, 0.1],
    },
    "lightgbm": {
        "model__n_estimators": [100, 200, 300],
        "model__max_depth": [2, 3, 4],
        "model__learning_rate": [0.02, 0.05, 0.1],
    },
}
