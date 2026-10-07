"""Seed the database with demo users, students and predictions."""
from __future__ import annotations

import os

from .extensions import db
from .models import Student, User


DEFAULT_USERS = [
    {
        "username": "admin",
        "full_name": "System Administrator",
        "email": "admin@university.edu",
        "role": "admin",
        "password": os.environ.get("SEED_ADMIN_PASSWORD", "Admin@12345"),
    },
    {
        "username": "lecturer",
        "full_name": "Dr. Lecturer",
        "email": "lecturer@university.edu",
        "role": "lecturer",
        "password": os.environ.get("SEED_LECTURER_PASSWORD", "Lecturer@1234"),
    },
    {
        "username": "advisor",
        "full_name": "Ms. Academic Advisor",
        "email": "advisor@university.edu",
        "role": "advisor",
        "password": os.environ.get("SEED_ADVISOR_PASSWORD", "Advisor@1234"),
    },
]


def seed_users() -> list[User]:
    """Create the demo accounts (idempotent)."""
    users = []
    for spec in DEFAULT_USERS:
        user = User.query.filter_by(username=spec["username"]).first()
        if user is None:
            user = User(
                username=spec["username"],
                full_name=spec["full_name"],
                email=spec["email"],
                role=spec["role"],
            )
            user.set_password(spec["password"])
            db.session.add(user)
        users.append(user)
    db.session.flush()
    return users


def seed_students_and_predictions(limit: int | None = None) -> tuple[int, int]:
    """Import the training CSV into the database and score every student."""
    from .config import MODEL_PATH, TRAINING_DATA_PATH
    from .services.data_service import _upsert_students
    from .services.prediction_service import predict_and_store

    if Student.query.count() > 0:
        return Student.query.count(), 0
    if not os.path.exists(TRAINING_DATA_PATH):
        return 0, 0

    import pandas as pd

    from .ml.preprocess import clean_dataset

    frame = pd.read_csv(TRAINING_DATA_PATH)
    cleaned = clean_dataset(frame, require_target=True)
    if limit:
        cleaned = cleaned.head(limit)

    students, _ = _upsert_students(cleaned)
    db.session.flush()

    scored = 0
    try:
        predictions = predict_and_store(students)
        scored = len(predictions)
    except Exception as exc:  # model missing: still keep the students
        print(f"Predictions skipped during seeding: {exc}")

    return len(students), scored


def seed_database(limit: int | None = None) -> dict:
    """Full seed: users + students + predictions. Safe to re-run."""
    seed_users()
    students, scored = seed_students_and_predictions(limit=limit)
    db.session.commit()
    return {
        "users": len(DEFAULT_USERS),
        "students": students,
        "predictions": scored,
    }
