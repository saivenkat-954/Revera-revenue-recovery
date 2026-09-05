from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "data" / "revenue_events.csv"
ARTIFACT_DIR = ROOT / "backend" / "artifacts"
METRICS_PATH = ARTIFACT_DIR / "risk_metrics.json"

NUMERIC = [
    "amount", "attempt_count", "successful_payments", "failed_payments",
    "customer_age_days", "customer_lifetime_value", "days_since_last_payment",
    "checkout_duration_seconds", "prior_recovery_rate",
]
CATEGORICAL = ["event_type", "payment_method", "failure_reason"]
FEATURES = NUMERIC + CATEGORICAL
NUMERIC_IDX = list(range(len(NUMERIC)))
CATEGORICAL_IDX = list(range(len(NUMERIC), len(FEATURES)))


def _read_rows() -> list[dict[str, Any]]:
    with DATA_PATH.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _coerce(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        for key in NUMERIC:
            row[key] = float(row[key])
        row["recovered"] = int(row["recovered"])
    return rows


def _matrix(rows: list[dict[str, Any]]) -> np.ndarray:
    return np.array([[r[k] for k in FEATURES] for r in rows], dtype=object)


def train_model() -> dict[str, Any]:
    rows = _coerce(_read_rows())
    X = _matrix(rows)
    y = np.array([r["recovered"] for r in rows])
    groups = np.array([r["customer_id"] for r in rows])

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=20260901)
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))

    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_IDX),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_IDX),
    ])
    model = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=1200, class_weight="balanced")),
    ])
    model.fit(X[train_idx], y[train_idx])
    probs = model.predict_proba(X[test_idx])[:, 1]
    preds = (probs >= 0.5).astype(int)

    metrics = {
        "train_events": int(len(train_idx)),
        "test_events": int(len(test_idx)),
        "test_customers": int(len(set(groups[test_idx]))),
        "roc_auc": round(float(roc_auc_score(y[test_idx], probs)), 4),
        "precision": round(float(precision_score(y[test_idx], preds)), 4),
        "recall": round(float(recall_score(y[test_idx], preds)), 4),
        "f1": round(float(f1_score(y[test_idx], preds)), 4),
        "accuracy": round(float(accuracy_score(y[test_idx], preds)), 4),
        "brier_score": round(float(brier_score_loss(y[test_idx], probs)), 4),
        "split_strategy": "customer_group_holdout",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return {"model": model, "metrics": metrics}


class RiskEngine:
    def __init__(self) -> None:
        self.model = None
        self.metrics: dict[str, Any] = {}
        self.ready = False

    def initialize(self) -> dict[str, Any]:
        result = train_model()
        self.model = result["model"]
        self.metrics = result["metrics"]
        self.ready = True
        return self.metrics

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.ready:
            self.initialize()
        row = {k: payload.get(k) for k in FEATURES}
        for key in NUMERIC:
            row[key] = float(row[key] or 0)
        probability = float(self.model.predict_proba(_matrix([row]))[0, 1])
        amount = float(row["amount"])
        expected_recovery = amount * probability
        risk_score = min(1.0, probability * (0.55 + min(amount / 25000, 1.0) * 0.45))
        return {
            "recovery_probability": round(probability, 4),
            "expected_recovery": round(expected_recovery, 2),
            "risk_score": round(risk_score, 4),
            "recommendation": self.recommend(probability, expected_recovery, payload),
        }

    @staticmethod
    def recommend(probability: float, expected_recovery: float, payload: dict[str, Any]) -> str:
        attempts = int(payload.get("attempt_count", 0) or 0)
        contacts = int(payload.get("contacts_24h", 0) or 0)
        amount = float(payload.get("amount", 0) or 0)
        if contacts >= 2 or attempts >= 2:
            return "STOP"
        if probability < 0.18 or expected_recovery < 100:
            return "STOP"
        if amount > 25000:
            return "HUMAN_REVIEW"
        if probability >= 0.70:
            return "PAYMENT_LINK"
        if probability >= 0.50:
            return "ALTERNATIVE_METHOD"
        if probability >= 0.30:
            return "REMINDER"
        return "WAIT"


risk_engine = RiskEngine()
