"""SQLAlchemy models for the academic performance prediction system."""
from __future__ import annotations

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Roles
# --------------------------------------------------------------------------- #
ROLE_ADMIN = "admin"
ROLE_LECTURER = "lecturer"
ROLE_ADVISOR = "advisor"
ROLES = (ROLE_ADMIN, ROLE_LECTURER, ROLE_ADVISOR)

# Role capabilities (checked in blueprints / templates).
CAN_UPLOAD = (ROLE_ADMIN, ROLE_LECTURER)
CAN_INTERVENE = (ROLE_ADMIN, ROLE_ADVISOR)
CAN_MANAGE_USERS = (ROLE_ADMIN,)
CAN_VIEW_MODEL = (ROLE_ADMIN, ROLE_LECTURER)
CAN_VIEW_INTERVENTIONS = (ROLE_ADMIN, ROLE_ADVISOR)


class User(UserMixin, db.Model):
    """System user: administrator, lecturer or academic advisor."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_LECTURER)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active_flag = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    predictions = db.relationship("Prediction", back_populates="author", lazy="dynamic")
    interventions = db.relationship("Intervention", back_populates="advisor", lazy="dynamic")

    # -- password helpers ------------------------------------------------- #
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # -- flask-login ------------------------------------------------------ #
    @property
    def is_active(self) -> bool:  # noqa: D401 - flask-login contract
        return self.is_active_flag

    # -- role helpers ----------------------------------------------------- #
    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    def can(self, capability: str) -> bool:
        table = {
            "upload": CAN_UPLOAD,
            "intervene": CAN_INTERVENE,
            "manage_users": CAN_MANAGE_USERS,
            "view_model": CAN_VIEW_MODEL,
            "view_interventions": CAN_VIEW_INTERVENTIONS,
        }
        return self.role in table.get(capability, ())

    @property
    def role_label(self) -> str:
        return {
            ROLE_ADMIN: "Administrator",
            ROLE_LECTURER: "Lecturer",
            ROLE_ADVISOR: "Academic Advisor",
        }.get(self.role, self.role)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.username} ({self.role})>"


class Student(db.Model):
    """A student record as uploaded / imported into the system."""

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    programme = db.Column(db.String(80), nullable=False, default="Unknown")
    department = db.Column(db.String(80), nullable=False, default="Unknown")
    gender = db.Column(db.String(16), nullable=False, default="Unknown")
    age = db.Column(db.Integer, nullable=True)

    # Pre-examination predictors (mid-semester snapshot).
    previous_gpa = db.Column(db.Float, nullable=True)
    attendance_pct = db.Column(db.Float, nullable=True)
    assignment_score = db.Column(db.Float, nullable=True)
    quiz_score = db.Column(db.Float, nullable=True)
    mid_sem_score = db.Column(db.Float, nullable=True)
    continuous_assessment = db.Column(db.Float, nullable=True)
    study_hours = db.Column(db.Float, nullable=True)

    # Outcomes (ground truth, only available after examinations).
    exam_score = db.Column(db.Float, nullable=True)
    final_gpa = db.Column(db.Float, nullable=True)
    final_score = db.Column(db.Float, nullable=True)
    risk_level = db.Column(db.String(16), nullable=True, index=True)  # ground truth label

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    predictions = db.relationship(
        "Prediction", back_populates="student", cascade="all, delete-orphan", lazy="dynamic"
    )
    interventions = db.relationship(
        "Intervention", back_populates="student", cascade="all, delete-orphan", lazy="dynamic"
    )

    @property
    def latest_prediction(self):
        return self.predictions.order_by(Prediction.created_at.desc()).first()

    @property
    def predicted_risk(self) -> str | None:
        latest = self.latest_prediction
        return latest.risk_label if latest else None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Student {self.student_id}>"


class Prediction(db.Model):
    """One model inference for one student (single or batch upload)."""

    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    risk_level = db.Column(db.Integer, nullable=False)  # 0 low, 1 medium, 2 high
    risk_label = db.Column(db.String(16), nullable=False, index=True)
    confidence = db.Column(db.Float, nullable=False)
    prob_low = db.Column(db.Float, nullable=False)
    prob_medium = db.Column(db.Float, nullable=False)
    prob_high = db.Column(db.Float, nullable=False)

    # JSON blob: top contributing factors + generated recommendations.
    recommendations = db.Column(db.Text, nullable=True)
    feature_snapshot = db.Column(db.Text, nullable=True)

    model_version = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    student = db.relationship("Student", back_populates="predictions")
    author = db.relationship("User", back_populates="predictions")

    @property
    def recommendations_list(self) -> list[str]:
        import json

        if not self.recommendations:
            return []
        try:
            return json.loads(self.recommendations)
        except ValueError:  # pragma: no cover
            return []

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Prediction {self.id} {self.risk_label}>"


class DatasetUpload(db.Model):
    """Audit record for every CSV uploaded by a lecturer."""

    __tablename__ = "dataset_uploads"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    row_count = db.Column(db.Integer, default=0)
    accepted_rows = db.Column(db.Integer, default=0)
    rejected_rows = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), nullable=False, default="completed")
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("User")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DatasetUpload {self.filename} ({self.status})>"


class Intervention(db.Model):
    """An academic intervention recorded by an advisor for a student."""

    __tablename__ = "interventions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    advisor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("predictions.id"), nullable=True)

    action = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="planned")  # planned|in_progress|completed
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    student = db.relationship("Student", back_populates="interventions")
    advisor = db.relationship("User", back_populates="interventions")
    prediction = db.relationship("Prediction")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Intervention {self.id} {self.action}>"
