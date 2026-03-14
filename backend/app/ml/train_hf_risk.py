"""
Train HF risk model on UCI Heart Failure Clinical Records Dataset (Chicco & Jurman, 2020).
Run once: cd backend && python -m app.ml.train_hf_risk
Saves model.joblib and feature_medians.json under backend/app/ml/.
"""
from pathlib import Path
import json
import urllib.request

import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

ML_DIR = Path(__file__).parent
DATA_DIR = ML_DIR / "data"
UCI_CSV_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00519/heart_failure_clinical_records_dataset.csv"

FEATURE_COLUMNS = [
    "age",
    "anaemia",
    "creatinine_phosphokinase",
    "diabetes",
    "ejection_fraction",
    "high_blood_pressure",
    "platelets",
    "serum_creatinine",
    "serum_sodium",
    "sex",
    "smoking",
    "time",
]
TARGET = "DEATH_EVENT"


def download_dataset() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / "heart_failure_clinical_records_dataset.csv"
    if path.exists():
        return path
    urllib.request.urlretrieve(UCI_CSV_URL, path)
    return path


def main():
    path = download_dataset()
    df = pd.read_csv(path)
    if TARGET not in df.columns or not all(c in df.columns for c in FEATURE_COLUMNS):
        raise RuntimeError(f"Dataset missing required columns. Need {FEATURE_COLUMNS + [TARGET]}")
    X = df[FEATURE_COLUMNS].astype(float)
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    model = LogisticRegression(max_iter=500, random_state=42)
    model.fit(X_train_s, y_train)

    # Medians for imputation at inference (when app doesn't have lab values)
    feature_medians = X.median().to_dict()
    for k, v in feature_medians.items():
        feature_medians[k] = float(v)

    model_path = ML_DIR / "model.joblib"
    medians_path = ML_DIR / "feature_medians.json"
    joblib.dump({"model": model, "scaler": scaler, "feature_order": FEATURE_COLUMNS}, model_path)
    with open(medians_path, "w") as f:
        json.dump(feature_medians, f, indent=2)

    # Quick accuracy on test set
    X_test_s = scaler.transform(X_test)
    acc = (model.predict(X_test_s) == y_test).mean()
    print(f"UCI Heart Failure model trained. Test accuracy: {acc:.3f}")
    print(f"Saved {model_path} and {medians_path}")


if __name__ == "__main__":
    main()
