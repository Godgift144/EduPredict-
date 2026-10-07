"""Unit tests for the data-cleaning / feature pipeline."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.ml.preprocess import (
    FEATURE_COLUMNS,
    RISK_TO_LEVEL,
    clean_dataset,
    cohort_statistics,
    derive_target,
    normalise_columns,
)


def _messy_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Student ID": ["S1", "S2", "S2", "S3"],
            "Name": ["Ama", "Kofi", "Kofi", "Yaw"],
            "Programme": ["BSc CS", "BSc Maths", "BSc Maths", None],
            "Department": ["CS", "Maths", "Maths", "CS"],
            "Gender": ["Female", "Male", "Male", "Male"],
            "Age": [20, 21, 21, 200],          # 200 is out of range
            "Previous GPA": [3.5, 1.2, 1.2, 2.5],
            "Attendance": [90, 40, 40, 70],     # alias -> attendance_pct
            "Assignment Score": [80, 35, 35, 60],
            "Quiz Score": [75, 30, 30, 55],
            "Mid Semester Score": [78, 33, 33, 58],  # alias via 'mid_semester_score'?
            "CA": [77, 32, 32, 57],             # alias -> continuous_assessment
            "Study Hours": [15, 2, 2, 10],
            "Final Score": [82, 41, 41, 66],
        }
    )


def test_column_normalisation_applies_aliases():
    frame = normalise_columns(_messy_frame())
    assert "attendance_pct" in frame.columns
    assert "continuous_assessment" in frame.columns
    assert "student_id" in frame.columns
    assert "final_score" in frame.columns


def test_cleaning_removes_duplicates_and_imputes():
    cleaned = clean_dataset(_messy_frame(), require_target=True)
    # duplicate row removed
    assert len(cleaned) == 3
    # every feature column present with no NaNs
    assert not cleaned[FEATURE_COLUMNS].isna().any().any()
    # out-of-range age was nulled then imputed -> must be sane now
    assert cleaned["age"].between(15, 100).all()
    # no target leakage: target derived correctly for S1 (82 -> Low Risk)
    row = cleaned[cleaned["student_id"] == "S1"].iloc[0]
    assert row["risk_label"] == "Low Risk"


def test_target_bands():
    base = {c: [1.0, 1.0, 1.0] for c in FEATURE_COLUMNS}
    base["programme"] = ["A", "A", "A"]
    base["department"] = ["A", "A", "A"]
    base["gender"] = ["Male", "Male", "Male"]
    base["age"] = [20, 20, 20]
    base["final_score"] = [80.0, 60.0, 30.0]
    frame = pd.DataFrame(base)
    labelled = derive_target(frame)
    assert list(labelled["risk_label"]) == ["Low Risk", "Medium Risk", "High Risk"]
    assert list(labelled["risk_level"]) == [
        RISK_TO_LEVEL["Low Risk"],
        RISK_TO_LEVEL["Medium Risk"],
        RISK_TO_LEVEL["High Risk"],
    ]


def test_missing_target_rows_dropped():
    frame = _messy_frame()
    frame.loc[len(frame)] = frame.iloc[0].copy()
    frame.loc[len(frame) - 1, "Final Score"] = None  # not drop-target: NaN target
    cleaned = clean_dataset(frame, require_target=True)
    assert cleaned["risk_label"].notna().all()


def test_empty_dataset_raises():
    with pytest.raises(ValueError):
        clean_dataset(pd.DataFrame(), require_target=True)


def test_cohort_statistics_shape():
    cleaned = clean_dataset(_messy_frame(), require_target=True)
    stats = cohort_statistics(cleaned)
    assert "attendance_pct" in stats
    assert {"mean", "std", "median"} <= set(stats["attendance_pct"].keys())
    assert not np.isnan(stats["attendance_pct"]["mean"])
