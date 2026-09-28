"""
Phase 1 experiment runner: cardiovascular disease, primary study.

Two experiments, both using ONLY the training split for any fitting:

1. Within-site (Cleveland): stratified train/test split, RandomizedSearchCV
   hyperparameter tuning inside stratified K-fold CV on the training split
   only, final evaluation on the untouched held-out test split.

2. Cross-site generalization: models trained on the full Cleveland dataset
   (the most complete site - see missingness report) are evaluated, with NO
   further fitting, on the three other sites (Hungary/Switzerland/VA) as
   genuinely independent test sets from different institutions.

Run with: python -m src.diseases.cardio.run_experiment
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import mlflow
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.diseases.cardio.schema import (  # noqa: E402
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TARGET_BINARY,
)
from src.pipeline.data_loading import load_all_sites, load_site, missingness_report  # noqa: E402
from src.pipeline.evaluation import bootstrap_ci, compute_metrics, subgroup_performance  # noqa: E402
from src.pipeline.models import get_model_zoo  # noqa: E402
from src.pipeline.tuning import SEARCH_SPACES  # noqa: E402

RANDOM_STATE = 42
FEATURE_COLS = NUMERIC_FEATURES + CATEGORICAL_FEATURES
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

mlflow.set_tracking_uri(f"sqlite:///{ROOT / 'mlflow.db'}")
mlflow.set_experiment("cardio_primary_study")


def run_within_site_experiment() -> pd.DataFrame:
    print("=== Loading Cleveland (primary site) ===")
    df = load_site("cleveland")
    print(f"Rows: {len(df)} | Missing values per column:\n{df[FEATURE_COLS].isna().sum()}")

    X, y = df[FEATURE_COLS], df[TARGET_BINARY]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)} | Test prevalence: {y_test.mean():.3f}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    zoo = get_model_zoo()
    rows = []

    for name, pipeline in zoo.items():
        with mlflow.start_run(run_name=f"within_site_{name}"):
            if name in SEARCH_SPACES:
                search = RandomizedSearchCV(
                    pipeline,
                    SEARCH_SPACES[name],
                    n_iter=10,
                    scoring="roc_auc",
                    cv=cv,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
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
            metrics["roc_auc_ci_lower"] = lo
            metrics["roc_auc_ci_upper"] = hi

            mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
            print(f"{name:24s} ROC-AUC={metrics['roc_auc']:.3f} [{lo:.3f},{hi:.3f}]  "
                  f"PR-AUC={metrics['pr_auc']:.3f}  Brier={metrics['brier_score']:.3f}")

            rows.append({"model": name, **metrics})

            # Subgroup performance by sex, for the strongest-so-far reference model class
            if name in ("logistic_regression", "random_forest", "xgboost"):
                sg = subgroup_performance(y_test, y_prob, X_test["sex"], threshold=0.5)
                (REPORTS_DIR / f"subgroup_{name}.json").write_text(json.dumps(sg, indent=2))

    results = pd.DataFrame(rows).sort_values("roc_auc", ascending=False)
    results.to_csv(REPORTS_DIR / "cardio_within_site_results.csv", index=False)
    return results, fitted, zoo, cv, X_train, y_train, X_test, y_test


def run_cross_site_experiment(zoo: dict, X_train, y_train) -> pd.DataFrame:
    """Train on the full Cleveland training data (already fit above per
    model, refit here plainly for cross-site clarity), evaluate on the other
    three sites with zero further fitting - a genuine independent-site test,
    not a resplit of the same data."""
    print("\n=== Cross-site generalization (train=Cleveland, test=other sites) ===")
    other_sites = ["hungarian", "switzerland", "va"]
    rows = []

    for name in ["logistic_regression", "random_forest", "xgboost"]:
        pipeline = zoo[name]
        pipeline.fit(X_train, y_train)
        for site in other_sites:
            df_site = load_site(site)
            X_site, y_site = df_site[FEATURE_COLS], df_site[TARGET_BINARY]
            if y_site.nunique() < 2:
                continue
            y_prob = pipeline.predict_proba(X_site)[:, 1]
            metrics = compute_metrics(y_site, y_prob)
            print(f"{name:24s} -> {site:12s} ROC-AUC={metrics['roc_auc']:.3f}  "
                  f"n={len(X_site)}  prevalence={y_site.mean():.3f}")
            rows.append({"model": name, "test_site": site, "n": len(X_site), **metrics})

    results = pd.DataFrame(rows)
    results.to_csv(REPORTS_DIR / "cardio_cross_site_results.csv", index=False)
    return results


def run_missingness_report():
    df_all = load_all_sites()
    report = missingness_report(df_all)
    report.to_csv(REPORTS_DIR / "cardio_missingness_by_site.csv")
    print("\n=== Missingness by site (fraction NaN per column) ===")
    print(report)


if __name__ == "__main__":
    run_missingness_report()
    within_results, _, zoo, cv, X_train, y_train, X_test, y_test = run_within_site_experiment()
    cross_results = run_cross_site_experiment(zoo, X_train, y_train)

    print("\n=== Within-site results (sorted by ROC-AUC) ===")
    print(within_results.to_string(index=False))
