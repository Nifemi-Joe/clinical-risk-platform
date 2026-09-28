"""
Column schema for the UCI Heart Disease dataset (all four sites).

Source: Janosi, Steinbrunn, Pfisterer & Detrano (1988), "Heart Disease",
UCI Machine Learning Repository, DOI 10.24432/C52P4X, CC BY 4.0.

The 14-column "processed" files (Cleveland/Hungarian/Switzerland/VA) all
share this schema. Missing values are encoded as "?" in the raw files.
"""
from __future__ import annotations

COLUMN_NAMES = [
    "age",       # years
    "sex",       # 1 = male, 0 = female
    "cp",        # chest pain type: 1 typical angina, 2 atypical, 3 non-anginal, 4 asymptomatic
    "trestbps",  # resting blood pressure (mm Hg)
    "chol",      # serum cholesterol (mg/dl)
    "fbs",       # fasting blood sugar > 120 mg/dl (1 = true, 0 = false)
    "restecg",   # resting ECG results (0, 1, 2)
    "thalach",   # maximum heart rate achieved
    "exang",     # exercise-induced angina (1 = yes, 0 = no)
    "oldpeak",   # ST depression induced by exercise relative to rest
    "slope",     # slope of the peak exercise ST segment (1-3)
    "ca",        # number of major vessels (0-3) colored by fluoroscopy
    "thal",      # 3 = normal, 6 = fixed defect, 7 = reversible defect
    "num",       # raw target: 0 (no disease) - 4 (increasing severity)
]

# Numeric (continuous) vs categorical (discrete-coded) feature split, used to
# build the leakage-safe ColumnTransformer. This split reflects clinical
# meaning, not just dtype — e.g. `cp`, `restecg`, `slope`, `thal` are coded
# categories even though they're stored as numbers.
NUMERIC_FEATURES = ["age", "trestbps", "chol", "thalach", "oldpeak", "ca"]
CATEGORICAL_FEATURES = ["sex", "cp", "fbs", "restecg", "exang", "slope", "thal"]

TARGET_RAW = "num"
TARGET_BINARY = "target"

# Features flagged in the Stage-2 dataset review as diagnostic-workup outputs
# rather than pre-diagnostic risk factors (thal = thallium scan, ca =
# fluoroscopy). Kept in the primary model but tracked separately so we can
# report a sensitivity analysis with/without them, per the leakage concern
# raised during dataset evaluation.
WORKUP_DERIVED_FEATURES = ["ca", "thal"]

SITE_FILES = {
    "cleveland": "processed.cleveland.data",
    "hungarian": "processed.hungarian.data",
    "switzerland": "processed.switzerland.data",
    "va": "processed.va.data",
}
