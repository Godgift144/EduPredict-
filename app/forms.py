"""WTForms used across the web interface (CSRF-protected)."""
from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    InputRequired,
    Length,
    NumberRange,
    Optional,
)


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=64)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = StringField("Remember me")
    submit = SubmitField("Log in")


class UploadForm(FlaskForm):
    file = FileField(
        "Student records CSV",
        validators=[
            FileRequired(),
            FileAllowed(["csv"], "Only .csv files are allowed."),
        ],
    )
    predict_now = StringField(default="on")
    submit = SubmitField("Upload and predict")


class PredictForm(FlaskForm):
    student_id = StringField("Student ID", validators=[Optional(), Length(max=32)])
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    programme = StringField("Programme", validators=[Optional(), Length(max=80)], default="Unknown")
    department = StringField("Department", validators=[Optional(), Length(max=80)], default="Unknown")
    gender = SelectField(
        "Gender",
        choices=[
            ("Male", "Male"),
            ("Female", "Female"),
            ("Other", "Other"),
            ("Unknown", "Prefer not to say"),
        ],
        default="Unknown",
    )
    age = IntegerField("Age", validators=[Optional(), NumberRange(min=15, max=100)])
    previous_gpa = FloatField(
        "Previous GPA (0.00 - 4.00)",
        validators=[InputRequired(), NumberRange(min=0, max=4)],
    )
    attendance_pct = FloatField(
        "Attendance (%)",
        validators=[InputRequired(), NumberRange(min=0, max=100)],
    )
    assignment_score = FloatField(
        "Assignment score (%)",
        validators=[InputRequired(), NumberRange(min=0, max=100)],
    )
    quiz_score = FloatField(
        "Quiz score (%)",
        validators=[InputRequired(), NumberRange(min=0, max=100)],
    )
    mid_sem_score = FloatField(
        "Mid-semester score (%)",
        validators=[InputRequired(), NumberRange(min=0, max=100)],
    )
    continuous_assessment = FloatField(
        "Continuous assessment (%)",
        validators=[InputRequired(), NumberRange(min=0, max=100)],
    )
    study_hours = FloatField(
        "Study hours per week",
        validators=[Optional(), NumberRange(min=0, max=168)],
    )
    submit = SubmitField("Predict performance")


class UserForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=64)]
    )
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    role = SelectField(
        "Role",
        choices=[
            ("lecturer", "Lecturer"),
            ("advisor", "Academic Advisor"),
            ("admin", "Administrator"),
        ],
        default="lecturer",
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=128)]
    )
    submit = SubmitField("Create user")


class InterventionForm(FlaskForm):
    action = SelectField(
        "Intervention",
        choices=[
            ("Academic counselling", "Academic counselling"),
            ("Mentoring / tutoring", "Mentoring / tutoring"),
            ("Attendance follow-up", "Attendance follow-up"),
            ("Study skills workshop", "Study skills workshop"),
            ("Reduced course load", "Reduced course load"),
            ("Parent/guardian contact", "Parent/guardian contact"),
            ("Other", "Other"),
        ],
        default="Academic counselling",
    )
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=2000)])
    status = SelectField(
        "Status",
        choices=[("planned", "Planned"), ("in_progress", "In progress"), ("completed", "Completed")],
        default="planned",
    )
    submit = SubmitField("Record intervention")
