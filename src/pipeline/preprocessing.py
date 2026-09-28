"""
Leakage-safe preprocessing.

CRITICAL DESIGN RULE (per project methodology): every statistical
transformation here (imputation statistics, scaling parameters, encoding
categories) is wrapped in an sklearn ColumnTransformer/Pipeline. When this is
composed with cross-validation (via sklearn's Pipeline + cross_validate /
GridSearchCV / a manual CV loop), fit() is called ONLY on each training fold,
and transform() is applied to the held-out fold. No statistic computed here
ever sees test-fold data before the test fold is scored. This is what makes
the whole pipeline leakage-safe by construction rather than by discipline.
"""
from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.diseases.cardio.schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def build_preprocessor(
    numeric_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
) -> ColumnTransformer:
    """Build the leakage-safe preprocessing ColumnTransformer.

    Numeric: median imputation (robust to the outliers present in cholesterol
    / resting BP) + standard scaling (needed for LR/SVM/MLP; harmless for
    tree-based models).

    Categorical: most-frequent imputation + one-hot encoding. Most-frequent
    is a defensible default given the low cardinality of these clinical
    categories (2-4 levels each); it is documented here rather than silently
    assumed so it can be revisited in the sensitivity-analysis phase.
    """
    numeric_features = NUMERIC_FEATURES if numeric_features is None else numeric_features
    categorical_features = (
        CATEGORICAL_FEATURES if categorical_features is None else categorical_features
    )

    numeric_pipeline = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ]
    )
    return preprocessor
