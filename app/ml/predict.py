"""Model loading, inference, explanation and intervention recommendations."""
from __future__ import annotations

import json
import threading
from pathlib import Path

import joblib
import pandas as pd

from .preprocess import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    LEVEL_TO_RISK,
    NUMERIC_FEATURES,
    RISK_LABELS,
)

# --------------------------------------------------------------------------- #
# Model cache (reloaded automatically when the artefact changes on disk)
# --------------------------------------------------------------------------- #
_cache_lock = threading.Lock()
_cache: dict = {"path": None, "mtime": None, "bundle": None}


class ModelNotTrainedError(RuntimeError):
    """Raised when no trained model artefact exists yet."""


def load_bundle(model_path: str | Path, *, force: bool = False):
    model_path = Path(model_path)
    if not model_path.exists():
        raise ModelNotTrainedError(
            "No trained model found. Run 'python -m scripts.setup' or "
            "'python -m scripts.train' first."
        )
    mtime = model_path.stat().st_mtime
    with _cache_lock:
        if (
            not force
            and _cache["bundle"] is not None
            and _cache["path"] == str(model_path)
            and _cache["mtime"] == mtime
        ):
            return _cache["bundle"]
        bundle = joblib.load(model_path)
        _cache.update({"path": str(model_path), "mtime": mtime, "bundle": bundle})
        return bundle


def invalidate_cache() -> None:
    with _cache_lock:
        _cache.update({"path": None, "mtime": None, "bundle": None})


# --------------------------------------------------------------------------- #
# Recommendations
# --------------------------------------------------------------------------- #
FACTOR_ADVICE = {
    "attendance_pct": (
        "Attendance is below the cohort average — schedule a one-on-one "
        "meeting and monitor weekly attendance."
    ),
    "previous_gpa": (
        "Previous GPA indicates a weak academic foundation — enrol the "
        "student in a remedial/study-skills programme."
    ),
    "assignment_score": (
        "Assignment performance is lagging — provide assignment coaching "
        "and earlier draft deadlines."
    ),
    "quiz_score": (
        "Quiz scores are low — give additional practice quizzes and "
        "immediate feedback sessions."
    ),
    "mid_sem_score": (
        "Mid-semester performance is weak — review covered topics in an "
        "extra tutorial before the final examination."
    ),
    "continuous_assessment": (
        "Continuous-assessment marks are below par — audit how the student "
        "accumulates CA marks across courses."
    ),
    "study_hours": (
        "Reported study hours are low — agree on a structured weekly study "
        "plan with the advisor."
    ),
    "age": "Age profile differs from the cohort — check for non-traditional study constraints.",
}

RISK_BASELINE = {
    "High Risk": [
        "Flag the student for immediate academic intervention.",
        "Assign a mentor and review progress every two weeks.",
        "Consider a reduced course load or supplementary examination track.",
    ],
    "Medium Risk": [
        "Place the student on the academic watch-list for continuous monitoring.",
        "Encourage attendance at peer-led tutorial sessions.",
    ],
    "Low Risk": [
        "No intervention required — maintain current performance.",
        "Consider the student for peer tutoring or enrichment activities.",
    ],
}


def generate_recommendations(
    risk_label: str,
    record: dict,
    top_factors: list[str],
    cohort_stats: dict | None = None,
) -> list[str]:
    """Rule-based early-intervention recommendations.

    Combines risk-level baseline advice with factor-specific actions for the
    features that drove the prediction and sit below the cohort average.
    """
    recommendations: list[str] = []
    cohort_stats = cohort_stats or {}

    for factor in top_factors:
        if factor not in FACTOR_ADVICE:
            continue
        value = record.get(factor)
        stats = cohort_stats.get(factor)
        if (
            stats
            and isinstance(value, (int, float))
            and not pd.isna(value)
            and value < stats.get("mean", float("-inf"))
        ):
            recommendations.append(FACTOR_ADVICE[factor])

    recommendations.extend(RISK_BASELINE.get(risk_label, []))
    # De-duplicate, keep order, cap length.
    seen: set[str] = set()
    unique = []
    for rec in recommendations:
        if rec not in seen:
            seen.add(rec)
            unique.append(rec)
    return unique[:5]


# --------------------------------------------------------------------------- #
# Inference
# --------------------------------------------------------------------------- #
def _prepare_frame(records: list[dict]) -> pd.DataFrame:
    """Coerce an arbitrary list of record dicts into the model's schema."""
    df = pd.DataFrame(records)
    df = df.rename(
        columns=lambda c: str(c).strip().lower().replace(" ", "_") if c else c
    )
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    frame = df[FEATURE_COLUMNS].copy()
    for col in NUMERIC_FEATURES:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    for col in CATEGORICAL_FEATURES:
        frame[col] = frame[col].fillna("Unknown").astype(str).str.strip()
        frame[col] = frame[col].where(frame[col].str.len() > 0, "Unknown")
    return frame


def explain_record(
    record: dict, bundle: dict, proba: dict[str, float]
) -> tuple[list[str], dict]:
    """Rank the features that pushed a student towards higher risk."""
    importances = bundle.get("feature_importances") or []
    names = bundle.get("feature_names") or []
    stats = bundle.get("cohort_stats") or {}

    scored: list[tuple[str, float]] = []
    if importances and len(importances) == len(names):
        for name, importance in zip(names, importances):
            base = name.split(":")[0] if ": " in name else name
            if base not in NUMERIC_FEATURES:
                continue
            value = record.get(base)
            st = stats.get(base)
            if value is None or st is None:
                continue
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            std = st.get("std") or 1.0
            # Only credit features the student is *worse* than the cohort on.
            deficit = (st.get("mean", 0.0) - value) / (std if std else 1.0)
            if deficit > 0:
                scored.append((base, float(importance) * deficit))
    scored.sort(key=lambda kv: kv[1], reverse=True)
    top_factors = [name for name, _ in scored[:3]]

    explanation = {
        "top_factors": [
            {
                "feature": name,
                "value": record.get(name),
                "cohort_mean": round(stats.get(name, {}).get("mean", 0.0), 2),
                "score": round(score, 5),
            }
            for name, score in scored[:3]
        ],
        "probabilities": proba,
    }
    return top_factors, explanation


def predict_records(records: list[dict], model_path: str | Path) -> list[dict]:
    """Predict risk levels for a list of student record dictionaries."""
    if not records:
        return []
    bundle = load_bundle(model_path)
    pipeline = bundle["pipeline"]
    frame = _prepare_frame(records)

    proba_matrix = pipeline.predict_proba(frame)
    classes = list(pipeline.classes_)
    prob_by_class = {cls: proba_matrix[:, i] for i, cls in enumerate(classes)}

    results = []
    for idx, record in enumerate(records):
        probs = {cls: float(prob_by_class[cls][idx]) for cls in classes}
        best_label = max(probs, key=probs.get)
        confidence = probs[best_label]
        level = RISK_LABELS.index(best_label) if best_label in RISK_LABELS else 0

        prob_dict = {
            "Low Risk": probs.get("Low Risk", 0.0),
            "Medium Risk": probs.get("Medium Risk", 0.0),
            "High Risk": probs.get("High Risk", 0.0),
        }
        top_factors, explanation = explain_record(record, bundle, prob_dict)
        recommendations = generate_recommendations(
            best_label,
            {**{k: record.get(k) for k in FEATURE_COLUMNS}},
            top_factors,
            bundle.get("cohort_stats"),
        )
        results.append(
            {
                "risk_level": level,
                "risk_label": best_label,
                "confidence": round(confidence, 4),
                "prob_low": round(prob_dict["Low Risk"], 4),
                "prob_medium": round(prob_dict["Medium Risk"], 4),
                "prob_high": round(prob_dict["High Risk"], 4),
                "top_factors": top_factors,
                "explanation": explanation,
                "recommendations": recommendations,
                "model_name": bundle.get("model_name"),
                "model_version": bundle.get("model_version"),
            }
        )
    return results


def predict_single(record: dict, model_path: str | Path) -> dict:
    return predict_records([record], model_path)[0]


def model_info(model_path: str | Path) -> dict:
    """Metadata about the deployed model (never loads the pipeline twice)."""
    bundle = load_bundle(model_path)
    return {
        "model_name": bundle.get("model_name"),
        "model_version": bundle.get("model_version"),
        "trained_at": bundle.get("trained_at"),
        "training_rows": bundle.get("training_rows"),
        "risk_labels": bundle.get("risk_labels", RISK_LABELS),
        "features": bundle.get("feature_columns", FEATURE_COLUMNS),
    }


def dump_explanation(explanation: dict) -> str:
    return json.dumps(explanation, default=str)
