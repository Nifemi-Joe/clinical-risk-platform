"""
Evaluation metrics.

Deliberately does NOT include accuracy as a headline metric (per project
methodology - accuracy is misleading on imbalanced clinical targets). Core
set: ROC-AUC, PR-AUC (discrimination), Brier score (calibration), plus
bootstrap confidence intervals for robustness reporting instead of the full
formal hypothesis-testing battery (DeLong/McNemar) that was cut from the
portfolio-scope version of this project.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_metrics(y_true, y_prob, threshold: float = 0.5) -> dict:
    """Compute the core metric set for one set of predictions."""
    y_pred = (np.asarray(y_prob) >= threshold).astype(int)
    return {
        "roc_auc": roc_auc_score(y_true, y_prob),
        "pr_auc": average_precision_score(y_true, y_prob),
        "brier_score": brier_score_loss(y_true, y_prob),
        "sensitivity_recall": recall_score(y_true, y_pred),
        "specificity": recall_score(y_true, y_pred, pos_label=0),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
    }


def bootstrap_ci(
    y_true,
    y_prob,
    metric_fn=roc_auc_score,
    n_boot: int = 1000,
    ci: float = 0.95,
    random_state: int = 42,
) -> tuple[float, float, float]:
    """Bootstrap confidence interval for a metric, resampling with replacement
    at the patient level. Returns (point_estimate, lower, upper).

    Used instead of the full DeLong/McNemar hypothesis-testing battery from
    the original brief - gives an honest robustness picture (does the CI on
    two models' AUC overlap?) without the added complexity of formal paired
    tests, which was cut for portfolio scope."""
    rng = np.random.RandomState(random_state)
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    n = len(y_true)
    point = metric_fn(y_true, y_prob)

    boot_scores = []
    for _ in range(n_boot):
        idx = rng.randint(0, n, n)
        y_t, y_p = y_true[idx], y_prob[idx]
        if len(np.unique(y_t)) < 2:
            continue  # skip degenerate resamples where AUC is undefined
        boot_scores.append(metric_fn(y_t, y_p))

    alpha = (1 - ci) / 2
    lower = float(np.quantile(boot_scores, alpha))
    upper = float(np.quantile(boot_scores, 1 - alpha))
    return point, lower, upper


def subgroup_performance(y_true, y_prob, group_labels, threshold: float = 0.5) -> dict:
    """Discrimination + calibration metrics split by a demographic subgroup
    (e.g. sex). Per project methodology: report per-subgroup metrics, do not
    collapse to a single 'fairness score'."""
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    group_labels = np.asarray(group_labels)

    results = {}
    for group in np.unique(group_labels):
        mask = group_labels == group
        if mask.sum() < 5 or len(np.unique(y_true[mask])) < 2:
            results[str(group)] = {"n": int(mask.sum()), "note": "too few samples / single class"}
            continue
        results[str(group)] = {
            "n": int(mask.sum()),
            **compute_metrics(y_true[mask], y_prob[mask], threshold),
        }
    return results
