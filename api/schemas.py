"""
Pydantic schemas for the three /predict endpoints. Field names and
descriptions mirror the schema.py files in src/diseases/ - kept here rather
than imported directly so the API's public contract is explicit and
reviewable on its own, even though the underlying feature LIST is shared
with the training pipeline (validated by tests/test_api.py).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CardioInput(BaseModel):
    age: float = Field(..., ge=1, le=120, description="Age in years")
    sex: int = Field(..., ge=0, le=1, description="1 = male, 0 = female")
    cp: int = Field(..., ge=1, le=4, description="Chest pain type (1-4)")
    trestbps: float = Field(..., ge=50, le=260, description="Resting blood pressure (mm Hg)")
    chol: float = Field(..., ge=50, le=700, description="Serum cholesterol (mg/dl)")
    fbs: int = Field(..., ge=0, le=1, description="Fasting blood sugar > 120 mg/dl")
    restecg: int = Field(..., ge=0, le=2, description="Resting ECG result (0-2)")
    thalach: float = Field(..., ge=50, le=250, description="Max heart rate achieved")
    exang: int = Field(..., ge=0, le=1, description="Exercise-induced angina")
    oldpeak: float = Field(..., ge=0, le=10, description="ST depression vs. rest")
    slope: int = Field(..., ge=1, le=3, description="Slope of peak exercise ST segment")
    ca: int = Field(..., ge=0, le=3, description="Number of major vessels colored by fluoroscopy")
    thal: int = Field(..., description="3=normal, 6=fixed defect, 7=reversible defect")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "age": 63, "sex": 1, "cp": 1, "trestbps": 145, "chol": 233,
                "fbs": 1, "restecg": 2, "thalach": 150, "exang": 0,
                "oldpeak": 2.3, "slope": 3, "ca": 0, "thal": 6,
            }
        }
    )


class BreastCancerInput(BaseModel):
    """All 30 fields match the official UCI Wisconsin Diagnostic feature
    names (mean/standard-error/worst of 10 measured cell characteristics).
    Field names use underscores; mapped back to the original names
    ("mean radius" etc.) before being passed to the trained pipeline."""

    mean_radius: float
    mean_texture: float
    mean_perimeter: float
    mean_area: float
    mean_smoothness: float
    mean_compactness: float
    mean_concavity: float
    mean_concave_points: float
    mean_symmetry: float
    mean_fractal_dimension: float
    radius_error: float
    texture_error: float
    perimeter_error: float
    area_error: float
    smoothness_error: float
    compactness_error: float
    concavity_error: float
    concave_points_error: float
    symmetry_error: float
    fractal_dimension_error: float
    worst_radius: float
    worst_texture: float
    worst_perimeter: float
    worst_area: float
    worst_smoothness: float
    worst_compactness: float
    worst_concavity: float
    worst_concave_points: float
    worst_symmetry: float
    worst_fractal_dimension: float


class DiabetesInput(BaseModel):
    HighBP: int = Field(..., ge=0, le=1)
    HighChol: int = Field(..., ge=0, le=1)
    CholCheck: int = Field(..., ge=0, le=1)
    BMI: float = Field(..., ge=10, le=100)
    Smoker: int = Field(..., ge=0, le=1)
    Stroke: int = Field(..., ge=0, le=1)
    HeartDiseaseorAttack: int = Field(..., ge=0, le=1)
    PhysActivity: int = Field(..., ge=0, le=1)
    Fruits: int = Field(..., ge=0, le=1)
    Veggies: int = Field(..., ge=0, le=1)
    HvyAlcoholConsump: int = Field(..., ge=0, le=1)
    AnyHealthcare: int = Field(..., ge=0, le=1)
    NoDocbcCost: int = Field(..., ge=0, le=1)
    GenHlth: int = Field(..., ge=1, le=5, description="1=excellent ... 5=poor")
    MentHlth: float = Field(..., ge=0, le=30, description="Days of poor mental health, last 30 days")
    PhysHlth: float = Field(..., ge=0, le=30, description="Days of poor physical health, last 30 days")
    DiffWalk: int = Field(..., ge=0, le=1)
    Sex: int = Field(..., ge=0, le=1)
    Age: int = Field(..., ge=1, le=13, description="BRFSS age bucket code (1-13)")
    Education: int = Field(..., ge=1, le=6)
    Income: int = Field(..., ge=1, le=8)


class Contributor(BaseModel):
    feature: str
    contribution: float


class FeatureContribution(BaseModel):
    """One clinical variable's effect on THIS prediction, aggregated from
    the raw encoded model features and translated into plain language.
    See api/reporting.py for why aggregation is needed and how the
    translation is produced."""

    feature: str = Field(..., description="Underlying clinical variable name, e.g. 'thal'")
    label: str = Field(..., description="Human-readable name, e.g. 'Thalassemia test result'")
    patient_value: str = Field(..., description="This patient's submitted value, in plain words")
    contribution: float = Field(..., description="Signed, aggregated contribution to the prediction")
    direction: str = Field(..., description="'increased' | 'decreased' | 'had no effect on'")
    magnitude: str = Field(..., description="'strong' | 'moderate' | 'slight', relative to this row's own top contributors")


class MethodologySummary(BaseModel):
    """How this specific number was produced — model, attribution method,
    preprocessing, training data, and the real limitations of the method,
    not generic boilerplate."""

    model_family: str
    attribution_method: str
    preprocessing: str
    trained_on: str
    performance_summary: str
    selection_rationale: str
    limitations: list[str]


class PredictionResponse(BaseModel):
    disease: str
    model: str
    probability: float = Field(..., description="Predicted probability of the condition of concern")
    risk_band: str = Field(..., description="'low' | 'below-average' | 'elevated' | 'high'")
    calibration_context: str
    feature_contributions: list[FeatureContribution] = Field(
        default_factory=list,
        description="Aggregated, human-readable per-clinical-variable contributions (preferred over top_contributors)",
    )
    top_contributors: list[Contributor] = Field(
        default_factory=list,
        description="Raw encoded-feature contributions, kept for debugging/backward compatibility",
    )
    methodology: MethodologySummary
    disclaimer: str = (
        "This is a research prototype estimating the probability of the "
        "target outcome based on the provided variables. It is not a "
        "medical diagnosis and should not be used for clinical decision-making."
    )


# --- Auth & user management ---

class UserRegister(BaseModel):
    email: str
    password: str = Field(..., min_length=8)
    full_name: str
    role: str = Field(..., description="'patient' or 'doctor' - admin accounts are created by an existing admin, not self-registered")
    doctor_id: int | None = Field(None, description="Required if role='patient': the treating doctor's user id")


class UserLogin(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: int


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    doctor_id: int | None = None
    is_active: bool


# --- Messaging ---

class MessageCreate(BaseModel):
    recipient_id: int
    body: str = Field(..., min_length=1, max_length=5000)


class MessageOut(BaseModel):
    id: int
    sender_id: int
    sender_name: str
    recipient_id: int
    body: str
    read: bool
    created_at: str


# --- Prediction history ---

class PredictionRecord(BaseModel):
    id: int
    patient_id: int
    disease: str
    model_used: str
    probability: float
    created_at: str
