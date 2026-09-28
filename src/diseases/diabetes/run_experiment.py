"""
Phase 5: diabetes (imbalance/scale stress test, via the shared pipeline).

Same src/pipeline/ code as cardio and breast cancer - only schema, data
loading (with its documented subsample), and this orchestration script are
disease-specific. Two things make this run different from Phases 1/4:

1. A fixed, documented, stratified 15,000-row subsample (see schema.py) -
   the full 253,680-row grid across 9 tuned models was scoped out for
   runtime reasons, not hidden.
2. An explicit class-imbalance-handling comparison (class_weight="balanced"
   vs default), per the "class imbalance treatment" sensitivity analysis
   called for in the original project plan - added directly here rather
   than in the shared model zoo, since it's a disease-specific decision
   (cardio/breast cancer are far closer to balanced).

No cross-site generalization (single source) and no SHAP/calibration pass
in this first cut - flagged in "what's next," not silently skipped.
"""
from __future__ import annotations

import sys
from pathlib import Path

import mlflow
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.diseases.diabetes.data_loading import load_diabetes_df  # noqa: E402
from src.diseases.diabetes.schema import (  # noqa: E402
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    SUBSAMPLE_SIZE,
    TARGET_BINARY,
)
from src.pipeline.evaluation import bootstrap_ci, compute_metrics  # noqa: E402
from src.pipeline.models import get_model_zoo  # noqa: E402
from src.pipeline.preprocessing import build_preprocessor  # noqa: E402

RANDOM_STATE = 42
FEATURE_COLS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
REPORTS_DIR = ROOT / "reports"

mlflow.set_tracking_uri(f"sqlite:///{ROOT / 'mlflow.db'}")
mlflow.set_experiment("diabetes_secondary_study")


def run():
    df = load_diabetes_df(subsample=True)
    print(f"Using documented {SUBSAMPLE_SIZE}-row stratified subsample "
          f"(full dataset is 253,680 rows - see SOURCE_diabetes.md)")
    X, y = df[FEATURE_COLS], df[TARGET_BINARY]
    print(f"Rows: {len(df)} | Prevalence (diabetic): {y.mean():.3f}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # SAME shared model zoo as cardio/breast cancer - default (unweighted) models.
    zoo = get_model_zoo(numeric_features=NUMERIC_FEATURES, categorical_features=CATEGORICAL_FEATURES)
    # NOT tuning every model on 15k rows with the full search space here -
    # runtime tradeoff, flagged in "what's next." Fitting with defaults only
    # for this pass, using the shared zoo's already-reasonable defaults.
    rows = []

    for name, pipeline in zoo.items():
        with mlflow.start_run(run_name=f"diabetes_{name}"):
            pipeline.fit(X_train, y_train)
            y_prob = pipeline.predict_proba(X_test)[:, 1]
            metrics = compute_metrics(y_test, y_prob)
            point, lo, hi = bootstrap_ci(y_test, y_prob, roc_auc_score, n_boot=500)
            metrics["roc_auc_ci_lower"], metrics["roc_auc_ci_upper"] = lo, hi
            mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
            print(f"{name:24s} ROC-AUC={metrics['roc_auc']:.3f} [{lo:.3f},{hi:.3f}]  "
                  f"PR-AUC={metrics['pr_auc']:.3f}  Sens={metrics['sensitivity_recall']:.3f}")
            rows.append({"model": name, "variant": "default", **metrics})

    # --- Imbalance-handling ablation: class_weight="balanced" ---
    print("\n=== Imbalance-handling ablation (class_weight='balanced') ===")
    balanced_models = {
        "logistic_regression_balanced": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE
        ),
        "random_forest_balanced": RandomForestClassifier(
            n_estimators=300, max_depth=6, class_weight="balanced",
            random_state=RANDOM_STATE, n_jobs=-1,
        ),
    }
    for name, estimator in balanced_models.items():
        pipeline = Pipeline(steps=[
            ("preprocess", build_preprocessor(NUMERIC_FEATURES, CATEGORICAL_FEATURES)),
            ("model", estimator),
        ])
        with mlflow.start_run(run_name=f"diabetes_{name}"):
            pipeline.fit(X_train, y_train)
            y_prob = pipeline.predict_proba(X_test)[:, 1]
            metrics = compute_metrics(y_test, y_prob)
            point, lo, hi = bootstrap_ci(y_test, y_prob, roc_auc_score, n_boot=500)
            metrics["roc_auc_ci_lower"], metrics["roc_auc_ci_upper"] = lo, hi
            mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
            print(f"{name:24s} ROC-AUC={metrics['roc_auc']:.3f} [{lo:.3f},{hi:.3f}]  "
                  f"PR-AUC={metrics['pr_auc']:.3f}  Sens={metrics['sensitivity_recall']:.3f}")
            rows.append({"model": name, "variant": "balanced", **metrics})

    results = pd.DataFrame(rows).sort_values("roc_auc", ascending=False)
    results.to_csv(REPORTS_DIR / "diabetes_results.csv", index=False)
    print("\n=== Diabetes results (sorted by ROC-AUC) ===")
    print(results[["model", "variant", "roc_auc", "pr_auc", "sensitivity_recall",
                    "specificity", "brier_score"]].to_string(index=False))
    return results


if __name__ == "__main__":
    run()
