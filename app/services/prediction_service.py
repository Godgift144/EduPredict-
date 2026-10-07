"""Persisting model predictions and serving them to the web layer."""
from __future__ import annotations

import json
from pathlib import Path

from ..extensions import db
from ..ml.predict import predict_records
from ..models import Prediction, Student


def _snapshot(student: Student) -> dict:
    return {
        "student_id": student.student_id,
        "programme": student.programme,
        "department": student.department,
        "gender": student.gender,
        "age": student.age,
        "previous_gpa": student.previous_gpa,
        "attendance_pct": student.attendance_pct,
        "assignment_score": student.assignment_score,
        "quiz_score": student.quiz_score,
        "mid_sem_score": student.mid_sem_score,
        "continuous_assessment": student.continuous_assessment,
        "study_hours": student.study_hours,
    }


def predict_and_store(
    students: list[Student], *, user_id: int | None = None, model_path: str | Path | None = None
) -> list[Prediction]:
    """Batch-predict a list of (transient) Student objects and persist results."""
    from ..config import MODEL_PATH

    model_path = model_path or MODEL_PATH
    if not students:
        return []

    records = [_snapshot(s) for s in students]
    results = predict_records(records, model_path)

    predictions: list[Prediction] = []
    for student, result in zip(students, results):
        prediction = Prediction(
            student=student,
            user_id=user_id,
            risk_level=result["risk_level"],
            risk_label=result["risk_label"],
            confidence=result["confidence"],
            prob_low=result["prob_low"],
            prob_medium=result["prob_medium"],
            prob_high=result["prob_high"],
            recommendations=json.dumps(result["recommendations"]),
            feature_snapshot=json.dumps(
                {"explanation": result["explanation"]}, default=str
            ),
            model_version=result.get("model_version"),
        )
        db.session.add(prediction)
        predictions.append(prediction)
    db.session.flush()
    return predictions


def rerun_all(model_path: str | Path | None = None) -> int:
    """Re-score every student in the database (e.g. after retraining)."""
    students = Student.query.all()
    predict_and_store(students, model_path=model_path)
    db.session.commit()
    return len(students)


def prediction_summary() -> dict:
    """Risk distribution + headline numbers for the dashboard."""
    from sqlalchemy import func

    from ..models import Student

    total_students = db.session.query(func.count(Student.id)).scalar() or 0

    rows = (
        db.session.query(Prediction.risk_label, func.count(Prediction.id))
        .group_by(Prediction.risk_label)
        .all()
    )
    counts = {label: 0 for label in ("Low Risk", "Medium Risk", "High Risk")}
    for label, count in rows:
        counts[label] = count

    # Latest prediction per student only (avoid double counting).
    latest_ids = (
        db.session.query(func.max(Prediction.id)).group_by(Prediction.student_id).subquery()
    )
    latest_rows = (
        db.session.query(Prediction.risk_label, func.count(Prediction.id))
        .filter(Prediction.id.in_(db.session.query(latest_ids)))
        .group_by(Prediction.risk_label)
        .all()
    )
    latest = {label: 0 for label in counts}
    for label, count in latest_rows:
        latest[label] = count

    scored_students = sum(latest.values())
    high = latest.get("High Risk", 0)
    medium = latest.get("Medium Risk", 0)

    return {
        "total_students": total_students,
        "scored_students": scored_students,
        "risk_counts": latest,
        "high_risk": high,
        "medium_risk": medium,
        "low_risk": latest.get("Low Risk", 0),
        "high_risk_pct": round(100 * high / scored_students, 1) if scored_students else 0.0,
        "at_risk_pct": (
            round(100 * (high + medium) / scored_students, 1) if scored_students else 0.0
        ),
    }
