"""Dataset cleaning, feature/target definitions and the sklearn pipeline.

The modelling contract used across the whole system:

* **Features** are available *before* final examinations (mid-semester
  snapshot): demographics, previous GPA, attendance, assignment, quiz,
  mid-semester and continuous-assessment scores, and study hours.
* **Target** is the academic risk level derived from the final outcome:
  ``Low Risk`` (>= 70), ``Medium Risk`` (50-69), ``High Risk`` (< 50).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# --------------------------------------------------------------------------- #
# Feature schema
# --------------------------------------------------------------------------- #
NUMERIC_FEATURES = [
    "age",
    "previous_gpa",
    "attendance_pct",
    "assignment_score",
    "quiz_score",
    "mid_sem_score",
    "continuous_assessment",
    "study_hours",
]

CATEGORICAL_FEATURES = ["programme", "department", "gender"]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

TARGET_COLUMN = "risk_label"

# Risk classes ordered by severity.
RISK_LABELS = ["Low Risk", "Medium Risk", "High Risk"]
RISK_TO_LEVEL = {"Low Risk": 0, "Medium Risk": 1, "High Risk": 2}
LEVEL_TO_RISK = {v: k for k, v in RISK_TO_LEVEL.items()}

# Score bands used to derive the target from the final outcome.
LOW_RISK_MIN = 70.0
MEDIUM_RISK_MIN = 50.0

# Column aliases accepted from lecturer uploads (normalised, lower-case,
# spaces -> underscores) mapped onto the canonical schema.
COLUMN_ALIASES = {
    "matric_no": "student_id",
    "matric_number": "student_id",
    "matric": "student_id",
    "registration_number": "student_id",
    "name": "full_name",
    "student_name": "full_name",
    "attendance": "attendance_pct",
    "attendance_percentage": "attendance_pct",
    "attendance_rate": "attendance_pct",
    "assignment": "assignment_score",
    "assignments": "assignment_score",
    "quiz": "quiz_score",
    "quizzes": "quiz_score",
    "mid_semester": "mid_sem_score",
    "mid_semester_score": "mid_sem_score",
    "midsem": "mid_sem_score",
    "ca": "continuous_assessment",
    "continuous_assessment_score": "continuous_assessment",
    "exam": "exam_score",
    "examination": "exam_score",
    "examination_score": "exam_score",
    "final": "final_score",
    "total_score": "final_score",
    "gpa": "final_gpa",
    "prev_gpa": "previous_gpa",
    "study_time": "study_hours",
    "study_hours_per_week": "study_hours",
}

# Columns that must be present for an upload to be usable.
REQUIRED_FOR_PREDICTION = FEATURE_COLUMNS

# Columns that must be present for supervised training.
REQUIRED_FOR_TRAINING = FEATURE_COLUMNS + ["final_score"]

# Bounds used to sanitise values (out-of-range entries become missing and are
# then imputed, which is safer than silently trusting corrupt data).
NUMERIC_BOUNDS = {
    "age": (15, 100),
    "previous_gpa": (0.0, 4.0),
    "final_gpa": (0.0, 4.0),
    "attendance_pct": (0.0, 100.0),
    "assignment_score": (0.0, 100.0),
    "quiz_score": (0.0, 100.0),
    "mid_sem_score": (0.0, 100.0),
    "continuous_assessment": (0.0, 100.0),
    "exam_score": (0.0, 100.0),
    "final_score": (0.0, 100.0),
    "study_hours": (0.0, 168.0),
}


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lower-case, trim and alias-match column names onto the schema."""
    renamed = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_").replace("-", "_")
        key = "_".join(part for part in key.split("_") if part)
        renamed[col] = COLUMN_ALIASES.get(key, key)
    out = df.rename(columns=renamed)
    # If an alias collides with an existing canonical column, keep the first.
    return out.loc[:, ~out.columns.duplicated()]


def _coerce_and_bound(df: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric columns to numbers and null out-of-range values."""
    for col, (lo, hi) in NUMERIC_BOUNDS.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df.loc[(df[col] < lo) | (df[col] > hi), col] = np.nan
    for col in ("age",):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _impute(df: pd.DataFrame) -> pd.DataFrame:
    """Median-impute numeric columns, mode-impute categorical columns."""
    for col in NUMERIC_FEATURES + [c for c in NUMERIC_BOUNDS if c in df.columns]:
        if col in df.columns and df[col].isna().any():
            median = df[col].median()
            if pd.isna(median):
                median = 0.0
            df[col] = df[col].fillna(median)
    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            mode = df[col].mode(dropna=True)
            fill = mode.iloc[0] if len(mode) else "Unknown"
            df[col] = df[col].fillna(fill).astype(str).str.strip()
            df[col] = df[col].replace("", str(fill))
    return df


def ensure_student_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Create sequential student IDs when they are missing."""
    if "student_id" not in df.columns:
        df["student_id"] = None
    blank = df["student_id"].isna() | (df["student_id"].astype(str).str.strip() == "")
    if blank.any():
        start = 1
        df.loc[blank, "student_id"] = [
            f"STU{start + i:05d}" for i in range(int(blank.sum()))
        ]
    df["student_id"] = df["student_id"].astype(str).str.strip().str.upper()
    return df


def derive_target(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``final_score`` (if derivable) and the ``risk_label`` target."""
    df = df.copy()
    if "final_score" not in df.columns or df["final_score"].isna().all():
        if "exam_score" in df.columns:
            exam = pd.to_numeric(df.get("exam_score"), errors="coerce")
            ca = pd.to_numeric(df.get("continuous_assessment"), errors="coerce")
            df["final_score"] = 0.7 * exam + 0.3 * ca.fillna(exam)
        else:
            raise ValueError(
                "Cannot derive the target: dataset needs 'final_score' or 'exam_score'."
            )
    df["final_score"] = pd.to_numeric(df["final_score"], errors="coerce")

    def _band(score: float) -> str | None:
        if pd.isna(score):
            return None
        if score >= LOW_RISK_MIN:
            return "Low Risk"
        if score >= MEDIUM_RISK_MIN:
            return "Medium Risk"
        return "High Risk"

    df["risk_label"] = df["final_score"].apply(_band)
    if "risk_level" not in df.columns:
        df["risk_level"] = df["risk_label"].map(RISK_TO_LEVEL)
    return df


def clean_dataset(df: pd.DataFrame, *, require_target: bool = False) -> pd.DataFrame:
    """Full cleaning pipeline: dedupe, sanitise, impute, (optionally) label.

    Returns a frame guaranteed to contain every column in
    :data:`FEATURE_COLUMNS` with no missing values.
    """
    if df is None or len(df) == 0:
        raise ValueError("The dataset is empty.")

    out = normalise_columns(df.copy())
    out = out.drop_duplicates()
    out = ensure_student_ids(out)
    out = _coerce_and_bound(out)

    # Ensure the canonical feature columns exist.
    for col in CATEGORICAL_FEATURES:
        if col not in out.columns:
            out[col] = "Unknown"
    for col in NUMERIC_FEATURES:
        if col not in out.columns:
            out[col] = np.nan

    out = _impute(out)

    if require_target:
        out = derive_target(out)
        before = len(out)
        out = out.dropna(subset=["risk_label", "final_score"])
        dropped = before - len(out)
        if dropped:
            # Keep the report honest: rows without an outcome cannot train.
            out = out.reset_index(drop=True)
        if len(out) == 0:
            raise ValueError("No rows with a valid final outcome were found.")

    # Human-friendly categorical formatting.
    for col in CATEGORICAL_FEATURES:
        out[col] = out[col].astype(str).str.strip()
        out[col] = out[col].where(out[col].str.len() > 0, "Unknown")

    return out.reset_index(drop=True)


def build_preprocessor() -> ColumnTransformer:
    """Scaling for numeric features + one-hot encoding for categoricals."""
    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, NUMERIC_FEATURES),
            ("cat", categorical_pipe, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def cohort_statistics(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Cohort mean/std per numeric feature — used to explain predictions."""
    stats: dict[str, dict[str, float]] = {}
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce")
            stats[col] = {
                "mean": float(series.mean()) if series.notna().any() else 0.0,
                "std": float(series.std()) if series.notna().any() else 1.0,
                "median": float(series.median()) if series.notna().any() else 0.0,
            }
    return stats
