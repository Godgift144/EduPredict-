"""Shared pytest fixtures for the EduRisk Predictor test suite."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from app.models import Student, User  # noqa: E402

LECTURER = {"username": "lecturer", "password": "Lecturer@1234"}
ADVISOR = {"username": "advisor", "password": "Advisor@1234"}
ADMIN = {"username": "admin", "password": "Admin@12345"}


@pytest.fixture(scope="session")
def app():
    """Application instance backed by an in-memory database.

    NOTE: the app context must NOT stay open across requests — Flask-Login
    caches the current user in ``g`` (app context), which would leak the same
    user into every test client.
    """
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        _seed_users()
    yield application
    with application.app_context():
        _db.session.remove()
        _db.drop_all()


def _seed_users() -> None:
    for spec in (LECTURER, ADVISOR, ADMIN):
        role = spec["username"]
        if User.query.filter_by(username=spec["username"]).first():
            continue
        user = User(
            username=spec["username"],
            full_name=spec["username"].title(),
            email=f"{spec['username']}@university.edu",
            role=role,
        )
        user.set_password(spec["password"])
        _db.session.add(user)
    _db.session.commit()


@pytest.fixture(scope="session")
def model_ready(app):
    """Make sure a trained model artefact exists (train a small one if not)."""
    from app.config import ARTIFACTS_DIR, MODEL_PATH, RAW_DATA_DIR, TRAINING_DATA_PATH

    if os.path.exists(MODEL_PATH):
        return MODEL_PATH
    # Bootstrap a small dataset + model for the test run.
    from scripts.generate_dataset import generate

    from app.ml.train import train_experiment

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not os.path.exists(TRAINING_DATA_PATH):
        generate(600).to_csv(TRAINING_DATA_PATH, index=False)
    train_experiment(TRAINING_DATA_PATH, ARTIFACTS_DIR, verbose=False)
    return MODEL_PATH


@pytest.fixture
def client(app, model_ready):
    return app.test_client()


def login(client, spec: dict):
    return client.post(
        "/login",
        data={"username": spec["username"], "password": spec["password"]},
        follow_redirects=False,
    )


@pytest.fixture
def lecturer_client(app, model_ready):
    client = app.test_client()
    login(client, LECTURER)
    return client


@pytest.fixture
def advisor_client(app, model_ready):
    client = app.test_client()
    login(client, ADVISOR)
    return client


@pytest.fixture
def admin_client(app, model_ready):
    client = app.test_client()
    login(client, ADMIN)
    return client


@pytest.fixture
def sample_csv_bytes():
    """A small CSV of two brand-new students (one clearly at risk)."""
    header = (
        "student_id,full_name,programme,department,gender,age,previous_gpa,"
        "attendance_pct,assignment_score,quiz_score,mid_sem_score,"
        "continuous_assessment,study_hours,exam_score,final_score\n"
    )
    rows = (
        "TEST90001,Test High Risk Student,BSc Computer Science,Computer Science,Male,20,"
        "1.40,35,30,28,32,30,2,35,36.5\n"
        "TEST90002,Test Low Risk Student,BSc Mathematics,Mathematics,Female,22,"
        "3.70,95,92,90,93,92,25,94,93.5\n"
    )
    return io.BytesIO((header + rows).encode("utf-8"))
