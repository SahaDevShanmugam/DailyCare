"""
Compute HF risk score from patient + vitals + symptoms using the UCI-trained model.
Returns 0-100 score and tier (low / moderate / high). Uses feature imputation for missing lab/clinical data.
"""
from pathlib import Path
import json
from typing import Optional
from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd

ML_DIR = Path(__file__).parent
MODEL_PATH = ML_DIR / "model.joblib"
MEDIANS_PATH = ML_DIR / "feature_medians.json"

DATASET_NAME = "UCI Heart Failure Clinical Records Dataset (Chicco & Jurman, 2020)"
FEATURE_ORDER = [
    "age", "anaemia", "creatinine_phosphokinase", "diabetes", "ejection_fraction",
    "high_blood_pressure", "platelets", "serum_creatinine", "serum_sodium",
    "sex", "smoking", "time",
]


@dataclass
class RiskResult:
    score: int  # 0-100
    tier: str  # "low" | "moderate" | "high"
    dataset_name: str
    disclaimer: str


def _load_model():
    if not MODEL_PATH.exists():
        return None
    data = joblib.load(MODEL_PATH)
    return data.get("model"), data.get("scaler"), data.get("feature_order", FEATURE_ORDER)


def _load_medians() -> dict:
    if not MEDIANS_PATH.exists():
        return {}
    with open(MEDIANS_PATH) as f:
        return json.load(f)


def _build_features(
    age: Optional[int] = None,
    sex: Optional[str] = None,
    vitals_sbp: Optional[list] = None,
    vitals_dbp: Optional[list] = None,
    vitals_hr: Optional[list] = None,
    vitals_weight: Optional[list] = None,
    symptom_count_7d: int = 0,
    medians: Optional[dict] = None,
) -> np.ndarray:
    """Build feature vector in UCI order; use medians for missing."""
    medians = medians or _load_medians()
    if not medians:
        return None
    vitals_sbp = vitals_sbp or []
    vitals_dbp = vitals_dbp or []
    vitals_hr = vitals_hr or []
    vitals_weight = vitals_weight or []

    def num(x):
        return float(x) if x is not None else np.nan

    age_val = num(age) if age is not None else medians.get("age", 60)
    sex_val = 1.0 if (sex and str(sex).upper().startswith("M")) else (0.0 if (sex and str(sex).upper().startswith("F")) else medians.get("sex", 0.5))
    mean_sbp = np.nanmean([num(x) for x in vitals_sbp if x is not None]) if vitals_sbp else np.nan
    high_bp = 1.0 if (mean_sbp >= 140) else (0.0 if not np.isnan(mean_sbp) else medians.get("high_blood_pressure", 0.5))

    features = [
        age_val,
        medians.get("anaemia", 0),
        medians.get("creatinine_phosphokinase", 250),
        medians.get("diabetes", 0),
        medians.get("ejection_fraction", 38),
        high_bp,
        medians.get("platelets", 263000),
        medians.get("serum_creatinine", 1.1),
        medians.get("serum_sodium", 136),
        sex_val,
        medians.get("smoking", 0),
        medians.get("time", 130),
    ]
    return np.array([features], dtype=np.float64)


def compute_risk(
    age: Optional[int] = None,
    sex: Optional[str] = None,
    vitals_sbp: Optional[list] = None,
    vitals_dbp: Optional[list] = None,
    vitals_hr: Optional[list] = None,
    vitals_weight: Optional[list] = None,
    symptom_count_7d: int = 0,
) -> RiskResult:
    """
    Compute HF risk score from available patient/vitals/symptom data.
    Missing UCI features are imputed with training-set medians.
    """
    disclaimer = (
        "For informational use only. Not a medical device. "
        "Based on a research dataset; discuss any concerns with your care team."
    )
    loaded = _load_model()
    if loaded is None:
        return RiskResult(score=0, tier="low", dataset_name=DATASET_NAME, disclaimer=disclaimer)
    model, scaler, order = loaded
    medians = _load_medians()
    if not medians:
        return RiskResult(
            score=0,
            tier="low",
            dataset_name=DATASET_NAME,
            disclaimer=disclaimer,
        )
    X = _build_features(
        age=age,
        sex=sex,
        vitals_sbp=vitals_sbp,
        vitals_dbp=vitals_dbp,
        vitals_hr=vitals_hr,
        vitals_weight=vitals_weight,
        symptom_count_7d=symptom_count_7d,
        medians=medians,
    )
    if X is None:
        return RiskResult(score=0, tier="low", dataset_name=DATASET_NAME, disclaimer=disclaimer)
    X = X[:, : len(order)] if X.shape[1] > len(order) else X
    X_df = pd.DataFrame(X, columns=order[: X.shape[1]])
    X_s = scaler.transform(X_df)
    prob = float(model.predict_proba(X_s)[0, 1])
    score = int(round(prob * 100))
    score = max(0, min(100, score))
    if score < 34:
        tier = "low"
    elif score < 67:
        tier = "moderate"
    else:
        tier = "high"
    return RiskResult(
        score=score,
        tier=tier,
        dataset_name=DATASET_NAME,
        disclaimer=disclaimer,
    )
