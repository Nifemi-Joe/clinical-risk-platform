"""
Turns raw model internals into a report a clinician or patient can actually
read, without a statistics background.

Two jobs live here, both direct fixes to a real problem seen in the deployed
UI: the "What influenced this estimate" list was showing raw, encoded
column names straight from the sklearn pipeline (e.g. `cat__thal_3.0`,
`cat__thal_7.0`, `num__ca`) with no indication of what value the patient
actually entered or what the code means.

1. AGGREGATION — a one-hot-encoded categorical feature like `thal` becomes
   several encoded columns (`cat__thal_3.0`, `cat__thal_6.0`,
   `cat__thal_7.0`). For a tree model, SHAP can assign a non-zero value to
   *every* one of those encoded columns for a single row (it explains
   deviation from an expected value, marginalizing over the feature's
   distribution) even though only one of them is actually "on" for this
   patient — that's why the screenshot that prompted this file showed both
   `thal_3.0` and `thal_7.0` in the same top-5 list, which reads as
   contradictory to anyone who doesn't already know how SHAP treats
   one-hot columns. `aggregate_contributions()` sums the encoded columns
   back to their single parent clinical variable before anything is shown,
   so the report has one row per real clinical input, not one row per
   encoding artifact.

2. TRANSLATION — the aggregated contribution is then paired with (a) a
   plain-English label for the clinical variable, (b) the patient's own
   submitted value rendered in words ("Reversible defect" rather than
   `7`), and (c) a plain-language methodology paragraph naming the model,
   the exact attribution method used, and this method's real limitations
   — instead of a bare percentage with no account of how it was produced.

Nothing here changes what the model computes. It only changes how the
model's own output is explained.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Feature label registries — one per disease, hand-written from each
# dataset's real documented codebook (UCI Heart Disease attribute
# information; UCI Wisconsin Diagnostic feature names; the 2015 BRFSS
# codebook for the diabetes survey fields). Nothing here is invented: every
# code->meaning mapping matches the source documentation already cited in
# src/diseases/*/schema.py and data/raw/SOURCE*.md.
# ---------------------------------------------------------------------------

CARDIO_LABELS: dict[str, dict] = {
    "age": {"label": "Age", "unit": "years"},
    "sex": {"label": "Sex", "values": {0: "Female", 1: "Male"}},
    "cp": {
        "label": "Chest pain type",
        "values": {
            1: "Typical angina",
            2: "Atypical angina",
            3: "Non-anginal pain",
            4: "Asymptomatic",
        },
    },
    "trestbps": {"label": "Resting blood pressure", "unit": "mm Hg"},
    "chol": {"label": "Serum cholesterol", "unit": "mg/dl"},
    "fbs": {
        "label": "Fasting blood sugar",
        "values": {0: "120 mg/dl or below", 1: "Above 120 mg/dl"},
    },
    "restecg": {
        "label": "Resting ECG result",
        "values": {
            0: "Normal",
            1: "ST-T wave abnormality",
            2: "Probable/definite left ventricular hypertrophy",
        },
    },
    "thalach": {"label": "Max heart rate achieved", "unit": "bpm"},
    "exang": {
        "label": "Exercise-induced angina",
        "values": {0: "No", 1: "Yes"},
    },
    "oldpeak": {"label": "ST depression (exercise vs. rest)", "unit": ""},
    "slope": {
        "label": "Slope of peak exercise ST segment",
        "values": {1: "Upsloping", 2: "Flat", 3: "Downsloping"},
    },
    "ca": {"label": "Major vessels seen on fluoroscopy", "unit": "vessels"},
    "thal": {
        "label": "Thalassemia test result",
        "values": {3: "Normal", 6: "Fixed defect", 7: "Reversible defect"},
    },
}

# Breast cancer's 30 features are all continuous, image-derived measurements
# with no coded categories, so labels are generated programmatically rather
# than hand-mapped — "mean concave points" -> "Mean concave points" — with
# units attached by which of the three measurement groups (mean / se /
# worst) the feature belongs to.
_BC_UNIT_HINT = "cell nuclei measurement, arbitrary imaging units"


def _breast_cancer_label(col: str) -> dict:
    return {"label": col[:1].upper() + col[1:], "unit": _BC_UNIT_HINT}


DIABETES_LABELS: dict[str, dict] = {
    "HighBP": {"label": "High blood pressure", "values": {0: "No", 1: "Yes"}},
    "HighChol": {"label": "High cholesterol", "values": {0: "No", 1: "Yes"}},
    "CholCheck": {"label": "Cholesterol checked in last 5 years", "values": {0: "No", 1: "Yes"}},
    "BMI": {"label": "Body mass index (BMI)", "unit": ""},
    "Smoker": {"label": "Smoked 100+ cigarettes in lifetime", "values": {0: "No", 1: "Yes"}},
    "Stroke": {"label": "Ever told had a stroke", "values": {0: "No", 1: "Yes"}},
    "HeartDiseaseorAttack": {
        "label": "Coronary heart disease or heart attack history",
        "values": {0: "No", 1: "Yes"},
    },
    "PhysActivity": {"label": "Physical activity in last 30 days", "values": {0: "No", 1: "Yes"}},
    "Fruits": {"label": "Eats fruit 1+ times/day", "values": {0: "No", 1: "Yes"}},
    "Veggies": {"label": "Eats vegetables 1+ times/day", "values": {0: "No", 1: "Yes"}},
    "HvyAlcoholConsump": {"label": "Heavy alcohol consumption", "values": {0: "No", 1: "Yes"}},
    "AnyHealthcare": {"label": "Has any healthcare coverage", "values": {0: "No", 1: "Yes"}},
    "NoDocbcCost": {"label": "Skipped a doctor visit due to cost", "values": {0: "No", 1: "Yes"}},
    "GenHlth": {
        "label": "Self-rated general health",
        "values": {1: "Excellent", 2: "Very good", 3: "Good", 4: "Fair", 5: "Poor"},
    },
    "MentHlth": {"label": "Poor mental health", "unit": "days in last 30"},
    "PhysHlth": {"label": "Poor physical health", "unit": "days in last 30"},
    "DiffWalk": {"label": "Serious difficulty walking/climbing stairs", "values": {0: "No", 1: "Yes"}},
    "Sex": {"label": "Sex", "values": {0: "Female", 1: "Male"}},
    "Age": {
        "label": "Age group (BRFSS bucket)",
        "values": {
            1: "18-24", 2: "25-29", 3: "30-34", 4: "35-39", 5: "40-44",
            6: "45-49", 7: "50-54", 8: "55-59", 9: "60-64", 10: "65-69",
            11: "70-74", 12: "75-79", 13: "80 or older",
        },
    },
    "Education": {
        "label": "Education level",
        "values": {
            1: "Never attended / kindergarten only",
            2: "Elementary (grades 1-8)",
            3: "Some high school (grades 9-11)",
            4: "High school graduate / GED",
            5: "Some college or technical school",
            6: "College graduate",
        },
    },
    "Income": {
        "label": "Household income bracket",
        "values": {
            1: "Under $10,000", 2: "$10,000-$14,999", 3: "$15,000-$19,999",
            4: "$20,000-$24,999", 5: "$25,000-$34,999", 6: "$35,000-$49,999",
            7: "$50,000-$74,999", 8: "$75,000 or more",
        },
    },
}

_REGISTRIES = {
    "cardiovascular": CARDIO_LABELS,
    "breast_cancer": {},  # generated programmatically, see _breast_cancer_label
    "diabetes": DIABETES_LABELS,
}


# ---------------------------------------------------------------------------
# Methodology text — one entry per (disease, model family) pair actually
# deployed, per src/registry/train_production_models.py's real selection
# rationale and real recorded metrics. Nothing here is generic boilerplate;
# each field is filled from that file's own metadata.json at request time
# in build_methodology(), this dict only supplies the parts that don't vary
# per-request (what the model family is, how attribution is computed, what
# its real limitations are).
# ---------------------------------------------------------------------------

_MODEL_EXPLANATIONS = {
    "random_forest": {
        "model_family": "Random Forest (an ensemble of decision trees)",
        "attribution_method": (
            "SHAP (SHapley Additive exPlanations), computed per-request with "
            "TreeExplainer. SHAP assigns each input feature a share of the "
            "difference between this prediction and the model's average "
            "prediction across its training data, using a game-theoretic "
            "method that is exact for tree ensembles (not an approximation)."
        ),
        "attribution_limitations": [
            "SHAP explains this one model's reasoning, not a causal claim "
            "about disease risk in general — a feature can show a large "
            "SHAP contribution without being a causal risk factor.",
            "Values are computed against the model's training data "
            "distribution; contributions are only meaningful relative to "
            "that reference population, not an absolute scale.",
        ],
    },
    "logistic_regression_l1": {
        "model_family": "Logistic Regression (L1-regularized, linear model)",
        "attribution_method": (
            "Exact linear decomposition: each feature's contribution is its "
            "fitted coefficient multiplied by this patient's transformed "
            "feature value. Unlike SHAP for tree models, this is not an "
            "approximation or a sampling-based estimate — it is the literal "
            "arithmetic the model performs to reach its prediction."
        ),
        "attribution_limitations": [
            "A linear model cannot represent interactions between features "
            "(e.g. \"feature A only matters when feature B is high\") — if "
            "such interactions exist clinically, this model and its "
            "explanation both miss them.",
        ],
    },
    "logistic_regression_balanced": {
        "model_family": "Logistic Regression (linear model, class-balanced)",
        "attribution_method": (
            "Exact linear decomposition: each feature's contribution is its "
            "fitted coefficient multiplied by this patient's transformed "
            "feature value — the literal arithmetic behind the prediction, "
            "not an approximation."
        ),
        "attribution_limitations": [
            "This model was deliberately tuned to catch more true cases at "
            "the cost of more false alarms (see selection rationale below) "
            "— a probability from it should be read as \"worth a closer "
            "look\" rather than a precise likelihood.",
            "A linear model cannot represent interactions between features.",
        ],
    },
}

_PREPROCESSING_TEXT = {
    "cardiovascular": (
        "Numeric fields (age, blood pressure, cholesterol, max heart rate, "
        "ST depression, vessel count) were median-imputed and standardized; "
        "categorical fields (sex, chest pain type, fasting blood sugar, "
        "resting ECG, exercise angina, ST slope, thalassemia result) were "
        "most-frequent-imputed and one-hot encoded — all fitted only on "
        "training data, never on data being predicted on."
    ),
    "breast_cancer": (
        "All 30 fields are continuous cell-nuclei measurements from a "
        "digitized biopsy image; each was median-imputed and standardized "
        "using statistics computed only from training data."
    ),
    "diabetes": (
        "The three continuous fields (BMI, days of poor mental/physical "
        "health) were median-imputed and standardized; the eighteen "
        "survey-response fields were most-frequent-imputed and one-hot "
        "encoded — all fitted only on training data."
    ),
}


def _coerce_key(raw) -> object:
    """Category keys in the label dicts above are Python ints; the encoded
    column suffix ('3.0', '7.0', '1') arrives as a string. Try int, then
    float-then-int, before giving up and using the raw string."""
    try:
        return int(raw)
    except (TypeError, ValueError):
        pass
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return raw


def _split_encoded_name(encoded_name: str, categorical_features: list[str]) -> tuple[str, str | None]:
    """'num__age' -> ('age', None). 'cat__thal_7.0' -> ('thal', '7.0')."""
    prefix, _, rest = encoded_name.partition("__")
    if prefix != "cat":
        return rest, None
    for col in sorted(categorical_features, key=len, reverse=True):
        if rest == col or rest.startswith(col + "_"):
            suffix = rest[len(col) + 1:] if rest != col else None
            return col, suffix
    return rest, None


def _format_patient_value(disease: str, column: str, raw_value) -> str:
    if disease == "breast_cancer":
        try:
            return f"{float(raw_value):.3g}"
        except (TypeError, ValueError):
            return str(raw_value)
    registry = _REGISTRIES.get(disease, {})
    meta = registry.get(column, {})
    values = meta.get("values")
    if values:
        return str(values.get(_coerce_key(raw_value), raw_value))
    unit = meta.get("unit", "")
    try:
        num = float(raw_value)
        text = f"{num:g}"
    except (TypeError, ValueError):
        text = str(raw_value)
    return f"{text} {unit}".strip()


def _column_label(disease: str, column: str) -> str:
    if disease == "breast_cancer":
        return _breast_cancer_label(column)["label"]
    return _REGISTRIES.get(disease, {}).get(column, {}).get("label", column)


@dataclass
class FeatureContribution:
    feature: str
    label: str
    patient_value: str
    contribution: float
    direction: str
    magnitude: str


def aggregate_contributions(
    disease: str,
    feature_names: list[str],
    contributions: list[float],
    categorical_features: list[str],
    raw_input: dict,
    top_n: int = 6,
) -> list[FeatureContribution]:
    """Sum encoded-column SHAP/coefficient contributions back to their
    parent clinical variable, then attach the patient's real submitted
    value in plain words. See module docstring for why this aggregation
    step exists — it is what stops the same clinical variable (e.g.
    thalassemia result) appearing twice under two different encoded names.
    """
    totals: dict[str, float] = {}
    for name, contribution in zip(feature_names, contributions):
        column, _ = _split_encoded_name(name, categorical_features)
        totals[column] = totals.get(column, 0.0) + float(contribution)

    ranked = sorted(totals.items(), key=lambda kv: abs(kv[1]), reverse=True)[:top_n]
    if not ranked:
        return []
    max_abs = max(abs(v) for _, v in ranked) or 1.0

    results = []
    for column, total in ranked:
        ratio = abs(total) / max_abs
        magnitude = "strong" if ratio > 0.66 else "moderate" if ratio > 0.33 else "slight"
        results.append(
            FeatureContribution(
                feature=column,
                label=_column_label(disease, column),
                patient_value=_format_patient_value(disease, column, raw_input.get(column)),
                contribution=round(total, 4),
                direction="increased" if total > 0 else "decreased" if total < 0 else "had no effect on",
                magnitude=magnitude,
            )
        )
    return results


@dataclass
class Methodology:
    model_family: str
    attribution_method: str
    preprocessing: str
    trained_on: str
    performance_summary: str
    selection_rationale: str
    limitations: list[str] = field(default_factory=list)


def build_methodology(disease: str, metadata: dict) -> Methodology:
    model_key = metadata.get("model", "")
    explain = _MODEL_EXPLANATIONS.get(
        model_key,
        {
            "model_family": model_key or "unknown",
            "attribution_method": "Per-feature contribution to the prediction.",
            "attribution_limitations": [],
        },
    )
    perf_bits = [
        f"{k.replace('_', ' ')}: {v}"
        for k, v in metadata.items()
        if "roc_auc" in k or "sensitivity" in k or "specificity" in k
    ]
    general_limitations = [
        "This is a research prototype trained on a historical dataset "
        "(see \"trained on\" above) — it estimates a statistical "
        "association, not a clinical diagnosis, and has not been "
        "validated in a live clinical setting.",
    ]
    return Methodology(
        model_family=explain["model_family"],
        attribution_method=explain["attribution_method"],
        preprocessing=_PREPROCESSING_TEXT.get(disease, ""),
        trained_on=metadata.get("trained_on", ""),
        performance_summary="; ".join(perf_bits),
        selection_rationale=metadata.get("selection_rationale", ""),
        limitations=explain.get("attribution_limitations", []) + general_limitations,
    )


def risk_band(probability: float) -> str:
    if probability < 0.2:
        return "low"
    if probability < 0.5:
        return "below-average"
    if probability < 0.8:
        return "elevated"
    return "high"
