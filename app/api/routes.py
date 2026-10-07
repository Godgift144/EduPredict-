"""JSON REST API consumed by the dashboards and external integrations.

All endpoints are session-authenticated (log in through ``/login``) and
CSRF-protected; send the token from the ``<meta name="csrf-token">`` tag in
the ``X-CSRFToken`` header on writes.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func, or_, select

from ..extensions import db
from ..ml.predict import ModelNotTrainedError, model_info, predict_single
from ..models import Intervention, Prediction, Student, User
from ..services import data_service, prediction_service, report_service

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _json_error(message: str, status: int):
    return jsonify(error=message), status


# --------------------------------------------------------------------------- #
# System
# --------------------------------------------------------------------------- #
@api_bp.get("/health")
def health():
    model_ready = Path(current_app.config["MODEL_PATH"]).exists()
    db_ok = True
    try:
        db.session.execute(select(func.count()).select_from(User))
    except Exception:  # pragma: no cover - defensive
        db_ok = False
    status = "ok" if (db_ok and model_ready) else "degraded"
    return jsonify(
        status=status,
        database=db_ok,
        model_ready=model_ready,
        version=current_app.config.get("APP_VERSION", "1.0.0"),
    ), 200 if status == "ok" else 503


@api_bp.get("/model/info")
@login_required
def api_model_info():
    try:
        return jsonify(model_info(current_app.config["MODEL_PATH"]))
    except ModelNotTrainedError as exc:
        return _json_error(str(exc), 404)


@api_bp.get("/model/metrics")
@login_required
def api_model_metrics():
    path = current_app.config["METRICS_PATH"]
    if not os.path.exists(path):
        return _json_error("Model metrics not found — train the model first.", 404)
    with open(path, encoding="utf-8") as fh:
        return jsonify(json.load(fh))


# --------------------------------------------------------------------------- #
# Summary / analytics
# --------------------------------------------------------------------------- #
@api_bp.get("/summary")
@login_required
def api_summary():
    summary = prediction_service.prediction_summary()
    summary["department_distribution"] = report_service.department_distribution()
    summary["programme_distribution"] = report_service.programme_distribution()
    summary["score_bands"] = report_service.score_bands()
    return jsonify(summary)


@api_bp.get("/alerts")
@login_required
def api_alerts():
    limit = min(int(request.args.get("limit", 20) or 20), 100)
    rows = report_service.recent_at_risk(limit)
    return jsonify(
        [
            {
                "student_id": s.student_id,
                "name": s.full_name,
                "department": s.department,
                "risk": p.risk_label,
                "confidence": p.confidence,
                "predicted_at": p.created_at.isoformat(),
            }
            for s, p in rows
        ]
    )


# --------------------------------------------------------------------------- #
# Students
# --------------------------------------------------------------------------- #
def _student_payload(student: Student, prediction: Prediction | None = None) -> dict:
    prediction = prediction or student.latest_prediction
    payload = {
        "id": student.id,
        "student_id": student.student_id,
        "full_name": student.full_name,
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
        "final_score": student.final_score,
        "final_gpa": student.final_gpa,
    }
    if prediction:
        payload["prediction"] = {
            "risk": prediction.risk_label,
            "risk_level": prediction.risk_level,
            "confidence": prediction.confidence,
            "probabilities": {
                "Low Risk": prediction.prob_low,
                "Medium Risk": prediction.prob_medium,
                "High Risk": prediction.prob_high,
            },
            "recommendations": prediction.recommendations_list,
            "created_at": prediction.created_at.isoformat(),
            "model_version": prediction.model_version,
        }
    else:
        payload["prediction"] = None
    return payload


@api_bp.get("/students")
@login_required
def api_students():
    q = (request.args.get("q") or "").strip()
    risk = request.args.get("risk") or ""
    department = request.args.get("department") or ""
    page = max(int(request.args.get("page", 1) or 1), 1)
    per_page = min(int(request.args.get("per_page", 25) or 25), 100)

    sub = (
        db.session.query(
            Prediction.student_id.label("sid"),
            func.max(Prediction.id).label("max_id"),
        )
        .group_by(Prediction.student_id)
        .subquery()
    )
    query = (
        db.session.query(Student, Prediction)
        .outerjoin(sub, sub.c.sid == Student.id)
        .outerjoin(Prediction, Prediction.id == sub.c.max_id)
    )
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Student.student_id.ilike(like),
                Student.full_name.ilike(like),
            )
        )
    if risk:
        query = query.filter(Prediction.risk_label == risk)
    if department:
        query = query.filter(Student.department == department)

    total = query.count()
    rows = (
        query.order_by(Prediction.risk_level.desc(), Student.student_id)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return jsonify(
        items=[_student_payload(s, p) for s, p in rows],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page,
    )


@api_bp.get("/students/<int:student_pk>")
@login_required
def api_student_detail(student_pk):
    student = Student.query.get_or_404(student_pk)
    payload = _student_payload(student)
    payload["interventions"] = [
        {
            "action": i.action,
            "notes": i.notes,
            "status": i.status,
            "advisor": i.advisor.full_name if i.advisor else None,
            "created_at": i.created_at.isoformat(),
        }
        for i in student.interventions.order_by(Intervention.created_at.desc())
    ]
    return jsonify(payload)


@api_bp.post("/students/<int:student_pk>/interventions")
@login_required
def api_add_intervention(student_pk):
    if not current_user.can("intervene"):
        return _json_error("Only advisors and admins can record interventions.", 403)
    student = Student.query.get_or_404(student_pk)
    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip()
    if not action:
        return _json_error("'action' is required.", 400)
    intervention = Intervention(
        student=student,
        advisor_id=current_user.id,
        prediction_id=(student.latest_prediction.id if student.latest_prediction else None),
        action=action,
        notes=data.get("notes"),
        status=data.get("status") or "planned",
    )
    db.session.add(intervention)
    db.session.commit()
    return jsonify({"id": intervention.id, "status": intervention.status}), 201


# --------------------------------------------------------------------------- #
# Predictions
# --------------------------------------------------------------------------- #
@api_bp.post("/predict")
@login_required
def api_predict():
    data = request.get_json(silent=True) or {}
    if not data:
        return _json_error("A JSON object with student features is required.", 400)
    try:
        result = predict_single(data, current_app.config["MODEL_PATH"])
    except ModelNotTrainedError as exc:
        return _json_error(str(exc), 409)
    except Exception as exc:  # malformed records
        return _json_error(f"Could not score the record: {exc}", 400)
    return jsonify(result)


@api_bp.post("/upload")
@login_required
def api_upload():
    if not current_user.can("upload"):
        return _json_error("Only lecturers and admins can upload datasets.", 403)
    try:
        record = data_service.import_dataset(
            request.files.get("file"), user_id=current_user.id
        )
    except data_service.DatasetValidationError as exc:
        return _json_error(str(exc), 400)
    except ModelNotTrainedError as exc:
        return _json_error(str(exc), 409)
    return jsonify(
        id=record.id,
        filename=record.filename,
        rows=record.accepted_rows,
        status=record.status,
        message=record.message,
    ), 201


@api_bp.post("/model/retrain")
@login_required
def api_retrain():
    if not current_user.is_admin:
        return _json_error("Only administrators can retrain the model.", 403)
    from ..ml.train import train_experiment

    data_path = current_app.config["TRAINING_DATA_PATH"]
    if not os.path.exists(data_path):
        return _json_error("Training dataset not found.", 404)
    try:
        summary = train_experiment(
            data_path,
            current_app.config["ARTIFACTS_FOLDER"],
            verbose=False,
        )
    except Exception as exc:  # pragma: no cover - surfaces training errors
        return _json_error(f"Training failed: {exc}", 500)

    # Re-score everyone with the fresh model.
    try:
        count = prediction_service.rerun_all(current_app.config["MODEL_PATH"])
    except Exception:  # pragma: no cover
        count = 0
    return jsonify(
        best_model=summary["best_model"],
        accuracy=summary["best_metrics"]["accuracy"],
        rescored=count,
    ), 200


@api_bp.get("/reports/predictions.csv")
@login_required
def api_export():
    import io

    preds = report_service.latest_predictions()
    frame = data_service.predictions_frame(preds)
    buffer = io.BytesIO()
    frame.to_csv(buffer, index=False)
    buffer.seek(0)
    from flask import send_file

    return send_file(
        buffer,
        mimetype="text/csv",
        as_attachment=True,
        download_name="risk_predictions.csv",
    )
