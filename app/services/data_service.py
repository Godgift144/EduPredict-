"""Data ingestion: validating and importing lecturer CSV uploads."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
from werkzeug.datastructures import FileStorage

from ..extensions import db
from ..ml.preprocess import (
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    clean_dataset,
    normalise_columns,
)
from ..models import DatasetUpload, Student


class DatasetValidationError(ValueError):
    """Raised when an uploaded file cannot be used."""


def _read_upload(file: FileStorage) -> pd.DataFrame:
    if file is None or not file.filename:
        raise DatasetValidationError("No file was selected.")
    filename = file.filename.lower()
    if not filename.endswith((".csv", ".txt")):
        raise DatasetValidationError("Only CSV files are supported.")
    raw = file.read()
    if not raw:
        raise DatasetValidationError("The uploaded file is empty.")
    try:
        frame = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:  # pragma: no cover - pandas error message passthrough
        raise DatasetValidationError(f"Could not parse the CSV file: {exc}") from exc
    if frame.empty:
        raise DatasetValidationError("The CSV contains no data rows.")
    return frame


def validate_upload(file: FileStorage) -> pd.DataFrame:
    """Read a CSV upload and check that prediction columns exist."""
    frame = _read_upload(file)
    frame = normalise_columns(frame)
    missing = [c for c in FEATURE_COLUMNS if c not in frame.columns]
    if missing:
        raise DatasetValidationError(
            "Missing required column(s): " + ", ".join(missing)
        )
    return frame


def _upsert_students(frame: pd.DataFrame) -> tuple[list[Student], int]:
    """Insert or update students keyed by ``student_id``."""
    created, updated = 0, 0
    students: list[Student] = []
    # Single prefetch instead of a SELECT per row (N+1): on a remote database
    # a 2,500-row import would otherwise cost thousands of round-trips.
    records = frame.to_dict("records")
    sids = [str(r.get("student_id", "")).strip().upper() for r in records]
    existing: dict[str, Student | None] = dict.fromkeys(sids)
    if existing:
        for found in Student.query.filter(Student.student_id.in_(existing)):
            existing[found.student_id] = found
    for sid, row in zip(sids, records):
        values = {
            "full_name": str(row.get("full_name") or "Unknown").strip() or "Unknown",
            "programme": str(row.get("programme") or "Unknown"),
            "department": str(row.get("department") or "Unknown"),
            "gender": str(row.get("gender") or "Unknown"),
            "age": _as_int(row.get("age")),
            "previous_gpa": _as_float(row.get("previous_gpa")),
            "attendance_pct": _as_float(row.get("attendance_pct")),
            "assignment_score": _as_float(row.get("assignment_score")),
            "quiz_score": _as_float(row.get("quiz_score")),
            "mid_sem_score": _as_float(row.get("mid_sem_score")),
            "continuous_assessment": _as_float(row.get("continuous_assessment")),
            "study_hours": _as_float(row.get("study_hours")),
            "exam_score": _as_float(row.get("exam_score")),
            "final_gpa": _as_float(row.get("final_gpa")),
            "final_score": _as_float(row.get("final_score")),
            "risk_level": row.get("risk_label"),
        }
        student = existing.get(sid)
        if student is None:
            student = Student(student_id=sid, **values)
            db.session.add(student)
            existing[sid] = student
            created += 1
        else:
            for key, value in values.items():
                if value is not None and not (
                    isinstance(value, float) and pd.isna(value)
                ):
                    setattr(student, key, value)
            updated += 1
        students.append(student)
    db.session.flush()
    return students, created + updated


def _as_float(value):
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value):
    f = _as_float(value)
    return int(f) if f is not None else None


def import_dataset(
    file: FileStorage, user_id: int | None = None, *, predict: bool = True
) -> DatasetUpload:
    """Validate, clean, store and (optionally) score an uploaded CSV."""
    from ..config import MODEL_PATH
    from .prediction_service import predict_and_store

    frame = validate_upload(file)
    cleaned = clean_dataset(frame, require_target=False)

    students, _ = _upsert_students(cleaned)

    upload = DatasetUpload(
        filename=file.filename,
        user_id=user_id,
        row_count=len(cleaned),
        accepted_rows=len(cleaned),
        status="completed",
        message=f"{len(cleaned)} row(s) imported.",
    )
    db.session.add(upload)
    db.session.flush()

    try:
        if predict:
            predict_and_store(students, user_id=user_id)
    except Exception as exc:  # model missing should not lose the import
        upload.status = "imported_unscored"
        upload.message = (
            f"{len(cleaned)} row(s) imported, but predictions failed: {exc}"
        )

    db.session.commit()
    return upload


# --------------------------------------------------------------------------- #
# Export helpers
# --------------------------------------------------------------------------- #
EXPORT_COLUMNS = [
    "student_id",
    "full_name",
    "programme",
    "department",
    "attendance_pct",
    "previous_gpa",
    "assignment_score",
    "quiz_score",
    "mid_sem_score",
    "continuous_assessment",
    "predicted_risk",
    "confidence",
    "recommendations",
]


def predictions_frame(predictions) -> pd.DataFrame:
    """Build an exportable DataFrame from a Prediction query."""
    rows = []
    for pred in predictions:
        student = pred.student
        rows.append(
            {
                "student_id": student.student_id if student else "",
                "full_name": student.full_name if student else "",
                "programme": student.programme if student else "",
                "department": student.department if student else "",
                "attendance_pct": student.attendance_pct if student else None,
                "previous_gpa": student.previous_gpa if student else None,
                "assignment_score": student.assignment_score if student else None,
                "quiz_score": student.quiz_score if student else None,
                "mid_sem_score": student.mid_sem_score if student else None,
                "continuous_assessment": student.continuous_assessment if student else None,
                "predicted_risk": pred.risk_label,
                "confidence": pred.confidence,
                "recommendations": "; ".join(pred.recommendations_list),
            }
        )
    return pd.DataFrame(rows, columns=EXPORT_COLUMNS)


TEMPLATE_HEADER = [
    "student_id",
    "full_name",
    "programme",
    "department",
    "gender",
    "age",
    "previous_gpa",
    "attendance_pct",
    "assignment_score",
    "quiz_score",
    "mid_sem_score",
    "continuous_assessment",
    "study_hours",
    "exam_score",
    "final_score",
    "final_gpa",
]

TEMPLATE_ROWS = [
    [
        "STU90001", "Ama Mensah", "BSc Computer Science", "Computer Science",
        "Female", 20, 3.10, 82, 70, 68, 72, 75, 14, 76, 74.3, 3.05,
    ],
    [
        "STU90002", "Kofi Boateng", "BSc Business Administration",
        "Business Administration", "Male", 21, 2.10, 58, 45, 42, 48, 50, 6,
        46, 46.9, 1.80,
    ],
    [
        "STU90003", "Grace Osei", "BSc Mathematics", "Mathematics",
        "Female", 22, 3.60, 93, 88, 90, 91, 89, 20, 94, 93.1, 3.85,
    ],
]


def read_template() -> bytes:
    """Return the CSV upload template bytes (generated if missing)."""
    from ..config import RAW_DATA_DIR

    path = Path(RAW_DATA_DIR) / "student_records_template.csv"
    if not path.exists():
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        lines = [",".join(TEMPLATE_HEADER)]
        lines.extend(",".join(str(v) for v in row) for row in TEMPLATE_ROWS)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path.read_bytes()
