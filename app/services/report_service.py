"""Aggregations used by dashboards, reports and the JSON API."""
from __future__ import annotations

from sqlalchemy import func

from ..extensions import db
from ..models import Prediction, Student


def _latest_prediction_ids():
    """Subquery: the most recent prediction id per student."""
    return (
        db.session.query(func.max(Prediction.id))
        .group_by(Prediction.student_id)
        .subquery()
    )


def latest_predictions():
    """All latest predictions (one per student)."""
    sub = _latest_prediction_ids()
    return (
        Prediction.query.filter(Prediction.id.in_(db.session.query(sub)))
        .order_by(Prediction.created_at.desc())
        .all()
    )


def latest_prediction_query():
    """Joined query of Student + its latest Prediction."""
    sub = _latest_prediction_ids()
    return (
        db.session.query(Student, Prediction)
        .join(Prediction, Prediction.student_id == Student.id)
        .filter(Prediction.id.in_(db.session.query(sub)))
    )


def department_distribution() -> dict[str, dict[str, int]]:
    """Risk counts per department (latest prediction only)."""
    rows = (
        latest_prediction_query()
        .with_entities(Student.department, Prediction.risk_label)
        .all()
    )
    distribution: dict[str, dict[str, int]] = {}
    for department, label in rows:
        bucket = distribution.setdefault(
            department, {"Low Risk": 0, "Medium Risk": 0, "High Risk": 0}
        )
        bucket[label] = bucket.get(label, 0) + 1
    return distribution


def recent_at_risk(limit: int = 10) -> list[tuple[Student, Prediction]]:
    """Most recent high/medium risk students for the alert panel."""
    return (
        latest_prediction_query()
        .filter(Prediction.risk_label.in_(["High Risk", "Medium Risk"]))
        .order_by(
            # High risk first, then most recent.
            Prediction.risk_level.desc(),
            Prediction.created_at.desc(),
        )
        .limit(limit)
        .all()
    )


def top_at_risk(limit: int = 15) -> list[tuple[Student, Prediction]]:
    """Highest-confidence high-risk students (the advisor work-list)."""
    return (
        latest_prediction_query()
        .filter(Prediction.risk_label == "High Risk")
        .order_by(Prediction.confidence.desc())
        .limit(limit)
        .all()
    )


def programme_distribution() -> dict[str, int]:
    rows = latest_prediction_query().with_entities(Student.programme).all()
    counts: dict[str, int] = {}
    for (programme,) in rows:
        counts[programme] = counts.get(programme, 0) + 1
    return counts


def score_bands() -> dict[str, float]:
    """Headline statistics about ground-truth outcomes (when available)."""
    rows = db.session.query(Student.final_score).filter(Student.final_score.isnot(None)).all()
    scores = [r[0] for r in rows]
    if not scores:
        return {}
    scores_sorted = sorted(scores)
    n = len(scores_sorted)
    return {
        "count": n,
        "mean": round(sum(scores) / n, 2),
        "min": round(scores_sorted[0], 2),
        "max": round(scores_sorted[-1], 2),
        "median": round(scores_sorted[n // 2], 2),
        "pass_rate": round(100 * sum(1 for s in scores if s >= 50) / n, 1),
    }


# --------------------------------------------------------------------------- #
# Intervention / advisor work-list helpers
# --------------------------------------------------------------------------- #
AT_RISK_LABELS = ("High Risk", "Medium Risk")


def at_risk_students() -> list[tuple[Student, Prediction]]:
    """Latest predictions for medium/high-risk students, highest risk first."""
    return (
        latest_prediction_query()
        .filter(Prediction.risk_label.in_(AT_RISK_LABELS))
        .order_by(Prediction.risk_level.desc(), Prediction.confidence.desc())
        .all()
    )


def intervention_summary() -> dict:
    """Intervention statistics + coverage of the at-risk cohort."""
    from ..models import Intervention

    total = Intervention.query.count()
    by_status = dict(
        db.session.query(Intervention.status, func.count(Intervention.id))
        .group_by(Intervention.status)
        .all()
    )
    rows = at_risk_students()
    at_risk_ids = {s.id for s, _ in rows}
    high_ids = {s.id for s, p in rows if p.risk_label == "High Risk"}

    with_any = {
        r[0]
        for r in db.session.query(Intervention.student_id).distinct().all()
    }
    with_completed = {
        r[0]
        for r in db.session.query(Intervention.student_id)
        .filter(Intervention.status == "completed")
        .distinct()
        .all()
    }
    covered = at_risk_ids & with_any
    return {
        "total": total,
        "planned": by_status.get("planned", 0),
        "in_progress": by_status.get("in_progress", 0),
        "completed": by_status.get("completed", 0),
        "at_risk": len(at_risk_ids),
        "covered": len(covered),
        "uncovered": len(at_risk_ids - with_any),
        "coverage_pct": round(100 * len(covered) / len(at_risk_ids), 1) if at_risk_ids else 0.0,
        "high_risk": len(high_ids),
        "high_risk_uncovered": len(high_ids - with_any),
        "high_risk_completed": len(high_ids & with_completed),
    }


def priority_queue(limit: int = 25) -> list[tuple[Student, Prediction, Intervention | None]]:
    """At-risk students with their most recent intervention (if any)."""
    from ..models import Intervention

    rows = at_risk_students()[:limit]
    ids = [s.id for s, _ in rows]
    latest: dict[int, Intervention] = {}
    if ids:
        history = (
            Intervention.query.filter(Intervention.student_id.in_(ids))
            .order_by(Intervention.created_at.desc())
            .all()
        )
        for item in history:
            latest.setdefault(item.student_id, item)
    return [(s, p, latest.get(s.id)) for s, p in rows]


def all_interventions(status: str | None = None, limit: int = 500):
    """Most recent interventions, optionally filtered by status."""
    from ..models import Intervention

    query = Intervention.query
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Intervention.created_at.desc()).limit(limit).all()
