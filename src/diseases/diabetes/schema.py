"""
Column schema for the BRFSS-derived diabetes dataset.

See SOURCE_diabetes.md for the full, honest provenance chain - this is a
third-party-cleaned derivative of 2015 BRFSS survey data, not a direct CDC
release. Role in the project (per Stage-2 review): imbalance/scale stress
test on the shared pipeline, not a primary study.
"""
from __future__ import annotations

TARGET_BINARY = "Diabetes_binary"

# All 21 predictor columns are already numeric/binary-coded in this cleaned
# release. Most are themselves binary survey responses (0/1) rather than
# continuous clinical measurements - a real difference from cardiovascular
# and breast cancer, reflecting the self-report survey origin (see
# SOURCE_diabetes.md). Treated as "categorical" for the shared preprocessor
# (one-hot on already-binary columns is a harmless no-op via
# handle_unknown="ignore", but keeps the pipeline consistent) except for the
# three genuinely continuous/ordinal-scale columns.
NUMERIC_FEATURES = ["BMI", "MentHlth", "PhysHlth"]
CATEGORICAL_FEATURES = [
    "HighBP", "HighChol", "CholCheck", "Smoker", "Stroke",
    "HeartDiseaseorAttack", "PhysActivity", "Fruits", "Veggies",
    "HvyAlcoholConsump", "AnyHealthcare", "NoDocbcCost", "GenHlth",
    "DiffWalk", "Sex", "Age", "Education", "Income",
]

# Documented, fixed subsample size for the full model-comparison grid - see
# SOURCE_diabetes.md and the Stage-2 dataset review for why full-scale
# (253,680 rows) was scoped out of this pass rather than silently truncated
# without explanation.
SUBSAMPLE_SIZE = 15000
SUBSAMPLE_RANDOM_STATE = 42
