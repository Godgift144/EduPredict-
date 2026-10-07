"""Web pages: dashboards, student records, uploads, predictions, reports."""
from __future__ import annotations

import json
import math

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from ..decorators import roles_required
from ..extensions import db
from ..forms import InterventionForm, PredictForm, UploadForm, UserForm
from ..ml.predict import ModelNotTrainedError, predict_single
from ..models import (
    DatasetUpload,
    Intervention,
    Prediction,
    ROLES,
    ROLE_LECTURER,
    Student,
    User,
)
from ..services import data_service, prediction_service, report_service

main_bp = Blueprint("main", __name__)


# --------------------------------------------------------------------------- #
# Home / dashboard
# --------------------------------------------------------------------------- #
@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    role = current_user.role
    summary = prediction_service.prediction_summary()
    bands = report_service.score_bands()

    # Aggregations shared by every role (cheap group-bys over the local DB).
    dept_distribution = report_service.department_distribution()
    recent_alerts = report_service.recent_at_risk(8)
    intervention = report_service.intervention_summary()
    last_upload = DatasetUpload.query.order_by(DatasetUpload.created_at.desc()).first()
    upload_count = DatasetUpload.query.count()
    user_count = User.query.count()

    model_meta = {}
    try:
        from ..ml.predict import model_info

        model_meta = model_info(current_app.config["MODEL_PATH"])
    except ModelNotTrainedError:
        flash("No trained model found — run 'python -m scripts.setup' first.", "warning")

    # Role-specific workspace: each role sees the data it acts on.
    queue = None
    if role == "advisor":
        queue = report_service.priority_queue(10)

    return render_template(
        "dashboard.html",
        role=role,
        summary=summary,
        dept_distribution=dept_distribution,
        recent_alerts=recent_alerts,
        bands=bands,
        intervention=intervention,
        queue=queue,
        last_upload=last_upload,
        upload_count=upload_count,
        user_count=user_count,
        model_meta=model_meta,
    )


# --------------------------------------------------------------------------- #
# Students
# --------------------------------------------------------------------------- #
@main_bp.route("/students")
@login_required
def students():
    q = (request.args.get("q") or "").strip()
    risk = request.args.get("risk") or ""
    department = request.args.get("department") or ""
    page = max(int(request.args.get("page", 1) or 1), 1)
    per_page = current_app.config["STUDENTS_PER_PAGE"]

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
                Student.programme.ilike(like),
            )
        )
    if risk:
        query = query.filter(Prediction.risk_label == risk)
    if department:
        query = query.filter(Student.department == department)

    total = query.count()
    pages = max(math.ceil(total / per_page), 1)
    page = min(page, pages)
    rows = (
        query.order_by(
            Prediction.risk_level.desc().nullslast(), Student.student_id.asc()
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    departments = [
        r[0]
        for r in db.session.query(Student.department)
        .distinct()
        .order_by(Student.department)
        .all()
    ]

    return render_template(
        "students.html",
        rows=rows,
        q=q,
        risk=risk,
        department=department,
        departments=departments,
        page=page,
        pages=pages,
        total=total,
    )


@main_bp.route("/students/<int:student_pk>")
@login_required
def student_detail(student_pk):
    student = Student.query.get_or_404(student_pk)
    prediction = student.latest_prediction
    interventions = (
        Intervention.query.filter_by(student_id=student.id)
        .order_by(Intervention.created_at.desc())
        .all()
    )
    explanation = {}
    if prediction and prediction.feature_snapshot:
        try:
            explanation = json.loads(prediction.feature_snapshot).get("explanation", {})
        except ValueError:  # pragma: no cover
            explanation = {}

    cohort = {}
    try:
        from ..ml.predict import load_bundle

        cohort = load_bundle(current_app.config["MODEL_PATH"]).get("cohort_stats", {})
    except ModelNotTrainedError:
        pass

    comparison = []
    for feature, label in (
        ("attendance_pct", "Attendance (%)"),
        ("previous_gpa", "Previous GPA ×25 (%)"),
        ("assignment_score", "Assignment (%)"),
        ("quiz_score", "Quiz (%)"),
        ("mid_sem_score", "Mid-semester (%)"),
        ("continuous_assessment", "Continuous assessment (%)"),
    ):
        value = getattr(student, feature, None)
        if feature == "previous_gpa" and value is not None:
            value = round(value * 25, 1)
        mean = (cohort.get(feature) or {}).get("mean")
        if feature == "previous_gpa" and mean is not None:
            mean = round(mean * 25, 1)
        comparison.append({"label": label, "value": value, "cohort_mean": mean})

    return render_template(
        "student_detail.html",
        student=student,
        prediction=prediction,
        explanation=explanation,
        interventions=interventions,
        intervention_form=InterventionForm(),
        comparison=comparison,
        can_intervene=current_user.can("intervene"),
    )


@main_bp.route("/students/<int:student_pk>/interventions", methods=["POST"])
@login_required
@roles_required("admin", "advisor")
def add_intervention(student_pk):
    student = Student.query.get_or_404(student_pk)
    form = InterventionForm()
    if form.validate_on_submit():
        intervention = Intervention(
            student=student,
            advisor_id=current_user.id,
            prediction_id=(student.latest_prediction.id if student.latest_prediction else None),
            action=form.action.data,
            notes=form.notes.data,
            status=form.status.data,
        )
        db.session.add(intervention)
        db.session.commit()
        flash(f"Intervention recorded for {student.full_name}.", "success")
    else:
        flash("Could not record the intervention — check the form.", "warning")
    return redirect(url_for("main.student_detail", student_pk=student.id))


# --------------------------------------------------------------------------- #
# Upload
# --------------------------------------------------------------------------- #
@main_bp.route("/upload", methods=["GET", "POST"])
@login_required
@roles_required("admin", "lecturer")
def upload():
    form = UploadForm()
    result = None
    if form.validate_on_submit():
        try:
            upload_record = data_service.import_dataset(
                form.file.data,
                user_id=current_user.id,
                predict=bool(form.predict_now.data),
            )
            result = upload_record
            flash(
                f"Uploaded '{upload_record.filename}': {upload_record.accepted_rows} "
                f"row(s) imported. {upload_record.message}",
                "success",
            )
        except data_service.DatasetValidationError as exc:
            flash(str(exc), "danger")
        except ModelNotTrainedError as exc:
            flash(str(exc), "warning")
    elif request.method == "POST":
        flash("Invalid upload — check the file format.", "warning")

    history = (
        DatasetUpload.query.order_by(DatasetUpload.created_at.desc()).limit(10).all()
    )
    return render_template("upload.html", form=form, result=result, history=history)


@main_bp.route("/upload/template.csv")
@login_required
def upload_template():
    data = data_service.read_template()
    import io

    return send_file(
        io.BytesIO(data),
        mimetype="text/csv",
        as_attachment=True,
        download_name="student_records_template.csv",
    )


# --------------------------------------------------------------------------- #
# Single prediction
# --------------------------------------------------------------------------- #
@main_bp.route("/predict", methods=["GET", "POST"])
@login_required
def predict_page():
    form = PredictForm()
    result = None
    record = None

    if form.validate_on_submit():
        record = {
            "student_id": form.student_id.data or "",
            "full_name": form.full_name.data,
            "programme": form.programme.data or "Unknown",
            "department": form.department.data or "Unknown",
            "gender": form.gender.data,
            "age": form.age.data,
            "previous_gpa": form.previous_gpa.data,
            "attendance_pct": form.attendance_pct.data,
            "assignment_score": form.assignment_score.data,
            "quiz_score": form.quiz_score.data,
            "mid_sem_score": form.mid_sem_score.data,
            "continuous_assessment": form.continuous_assessment.data,
            "study_hours": form.study_hours.data,
        }
        try:
            result = predict_single(record, current_app.config["MODEL_PATH"])
        except ModelNotTrainedError as exc:
            flash(str(exc), "warning")
    elif request.method == "POST":
        flash("Please correct the highlighted fields.", "warning")

    return render_template("predict.html", form=form, result=result, record=record)


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #
@main_bp.route("/reports")
@login_required
def reports():
    summary = prediction_service.prediction_summary()
    dept_distribution = report_service.department_distribution()
    programme_distribution = report_service.programme_distribution()
    bands = report_service.score_bands()
    top = report_service.top_at_risk(10)

    metrics = None
    import os

    if os.path.exists(current_app.config["METRICS_PATH"]):
        with open(current_app.config["METRICS_PATH"], encoding="utf-8") as fh:
            metrics = json.load(fh)

    return render_template(
        "reports.html",
        summary=summary,
        dept_distribution=dept_distribution,
        programme_distribution=programme_distribution,
        bands=bands,
        top=top,
        metrics=metrics,
    )


@main_bp.route("/reports/export.csv")
@login_required
def export_predictions():
    import io

    preds = report_service.latest_predictions()
    frame = data_service.predictions_frame(preds)
    buffer = io.BytesIO()
    frame.to_csv(buffer, index=False)
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="text/csv",
        as_attachment=True,
        download_name="risk_predictions.csv",
    )


@main_bp.route("/plots/<path:filename>")
@login_required
def plot(filename):
    """Serve evaluation plots (confusion matrix, feature importance, …)."""
    return send_from_directory(current_app.config["PLOTS_FOLDER"], filename)


# --------------------------------------------------------------------------- #
# Model performance
# --------------------------------------------------------------------------- #
@main_bp.route("/interventions")
@login_required
@roles_required("admin", "advisor")
def interventions():
    """Advisor workspace: intervention log + at-risk queue."""
    status = (request.args.get("status") or "").strip()
    items = report_service.all_interventions(status or None, limit=500)
    summary = report_service.intervention_summary()
    queue = report_service.priority_queue(40)
    uncovered = [(s, p) for s, p, item in queue if item is None]
    return render_template(
        "interventions.html",
        items=items,
        status=status,
        summary=summary,
        queue=queue,
        uncovered=uncovered,
    )


@main_bp.route("/model")
@login_required
@roles_required("admin", "lecturer")
def model_page():
    import os

    metrics_path = current_app.config["METRICS_PATH"]
    if not os.path.exists(metrics_path):
        flash("The model has not been trained yet.", "warning")
        return render_template("model.html", metrics=None, model_meta={})

    with open(metrics_path, encoding="utf-8") as fh:
        metrics = json.load(fh)

    model_meta = {}
    try:
        from ..ml.predict import model_info

        model_meta = model_info(current_app.config["MODEL_PATH"])
    except ModelNotTrainedError:  # pragma: no cover
        pass

    return render_template("model.html", metrics=metrics, model_meta=model_meta)


# --------------------------------------------------------------------------- #
# User management (admin)
# --------------------------------------------------------------------------- #
@main_bp.route("/users", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def users():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data.strip()).first():
            flash("That username already exists.", "danger")
        elif User.query.filter_by(email=form.email.data.strip().lower()).first():
            flash("That email is already registered.", "danger")
        else:
            user = User(
                username=form.username.data.strip(),
                full_name=form.full_name.data.strip(),
                email=form.email.data.strip().lower(),
                role=form.role.data or ROLE_LECTURER,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash(f"User '{user.username}' created.", "success")
            return redirect(url_for("main.users"))
    elif request.method == "POST":
        flash("Could not create the user — check the form.", "warning")

    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("users.html", form=form, users=all_users, roles=ROLES)
