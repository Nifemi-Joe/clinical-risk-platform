"""
Phase 4: breast cancer (negative control / pipeline-reuse test).

Notice what this file does NOT contain: no preprocessing logic, no model
definitions, no metric implementations, no bootstrap CI code. All of that is
imported unchanged from src/pipeline/ - the same code that ran the
cardiovascular study. Only the schema/data loader (src/diseases/breast_cancer/)
and this run script are disease-specific, and this run script is almost pure
orchestration. That is the actual proof of the "one pipeline, three diseases"
architecture decision from the program plan - not a claim, a demonstrated
property of the code.

No cross-site generalization experiment here (single source, unlike cardio's
four sites) and no subgroup/fairness analysis (no demographic variables in
this dataset - see schema.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

import mlflow
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.diseases.breast_cancer.data_loading import load_breast_cancer_df  # noqa: E402
from src.diseases.breast_cancer.schema import NUMERIC_FEATURES, TARGET_BINARY  # noqa: E402
from src.pipeline.evaluation import bootstrap_ci, compute_metrics  # noqa: E402
from src.pipeline.models import get_model_zoo  # noqa: E402
from src.pipeline.tuning import SEARCH_SPACES  # noqa: E402

RANDOM_STATE = 42
REPORTS_DIR = ROOT / "reports"

mlflow.set_tracking_uri(f"sqlite:///{ROOT / 'mlflow.db'}")
mlflow.set_experiment("breast_cancer_secondary_study")


def run():
    df = load_breast_cancer_df()
    X, y = df[NUMERIC_FEATURES], df[TARGET_BINARY]
    print(f"Rows: {len(df)} | Missing values: {X.isna().sum().sum()} | "
          f"Prevalence (malignant): {y.mean():.3f}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    # SAME get_model_zoo() function as cardio - only the feature lists differ,
    # and there are no categorical features here at all.
    zoo = get_model_zoo(numeric_features=NUMERIC_FEATURES, categorical_features=[])
    rows = []

    for name, pipeline in zoo.items():
        with mlflow.start_run(run_name=f"breast_cancer_{name}"):
            if name in SEARCH_SPACES:
                search = RandomizedSearchCV(
                    pipeline, SEARCH_SPACES[name], n_iter=10, scoring="roc_auc",
                    cv=cv, random_state=RANDOM_STATE, n_jobs=-1,
                )
                search.fit(X_train, y_train)
                fitted = search.best_estimator_
                mlflow.log_params({k: str(v) for k, v in search.best_params_.items()})
            else:
                fitted = pipeline
                fitted.fit(X_train, y_train)

            y_prob = fitted.predict_proba(X_test)[:, 1]
            metrics = compute_metrics(y_test, y_prob)
            point, lo, hi = bootstrap_ci(y_test, y_prob, roc_auc_score, n_boot=1000)
            metrics["roc_auc_ci_lower"], metrics["roc_auc_ci_upper"] = lo, hi

            mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
            print(f"{name:24s} ROC-AUC={metrics['roc_auc']:.4f} [{lo:.4f},{hi:.4f}]  "
                  f"PR-AUC={metrics['pr_auc']:.4f}  Brier={metrics['brier_score']:.4f}")
            rows.append({"model": name, **metrics})

    results = pd.DataFrame(rows).sort_values("roc_auc", ascending=False)
    results.to_csv(REPORTS_DIR / "breast_cancer_results.csv", index=False)
    print("\n=== Breast cancer results (sorted by ROC-AUC) ===")
    print(results.to_string(index=False))
    return results


if __name__ == "__main__":
    run()
