"""Tests for training, inference and recommendation generation."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import pytest

from app.ml.predict import (
    ModelNotTrainedError,
    load_bundle,
    model_info,
    predict_records,
    predict_single,
)
from app.ml.preprocess import RISK_LABELS, clean_dataset
from app.ml.train import build_model_zoo, train_experiment

HIGH_RISK_RECORD = {
    "student_id": "T1",
    "full_name": "At Risk Student",
    "programme": "BSc Computer Science",
    "department": "Computer Science",
    "gender": "Male",
    "age": 20,
    "previous_gpa": 1.2,
    "attendance_pct": 32,
    "assignment_score": 28,
    "quiz_score": 30,
    "mid_sem_score": 25,
    "continuous_assessment": 27,
    "study_hours": 2,
}

LOW_RISK_RECORD = {
    "student_id": "T2",
    "full_name": "Excellent Student",
    "programme": "BSc Computer Science",
    "department": "Computer Science",
    "gender": "Female",
    "age": 21,
    "previous_gpa": 3.8,
    "attendance_pct": 96,
    "assignment_score": 93,
    "quiz_score": 91,
    "mid_sem_score": 94,
    "continuous_assessment": 92,
    "study_hours": 25,
}


def test_model_zoo_has_five_classifiers():
    zoo = build_model_zoo()
    assert len(zoo) == 5
    assert "Random Forest" in zoo


def test_training_produces_acceptable_metrics(app, model_ready):
    metrics_path = Path(model_ready).parent / "metrics.json"
    assert metrics_path.exists(), "metrics.json should be written during training"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    assert metrics["best_model"] in metrics["models"]
    assert set(metrics["models"]) == {
        "Random Forest",
        "Decision Tree",
        "Logistic Regression",
        "Naive Bayes",
        "Support Vector Machine",
    }
    best = metrics["best_metrics"]
    assert best["accuracy"] >= 0.70, "model must clear the 70% acceptance threshold"
    assert best["f1_weighted"] >= 0.70
    # Confusion matrix must be 3x3 over the documented risk labels.
    assert len(best["confusion_matrix"]) == 3
    assert best["labels"] == RISK_LABELS
    # Plots generated for the report.
    plots = Path(model_ready).parent / "plots"
    for name in ("confusion_matrix.png", "model_comparison.png", "class_distribution.png"):
        assert (plots / name).exists(), f"missing plot {name}"


def test_training_from_scratch_on_small_dataset(tmp_path):
    from scripts.generate_dataset import generate

    csv_path = tmp_path / "mini.csv"
    generate(500, seed=7).to_csv(csv_path, index=False)
    summary = train_experiment(csv_path, tmp_path / "artifacts", verbose=False)
    assert summary["best_metrics"]["accuracy"] >= 0.70
    assert (tmp_path / "artifacts" / "model.joblib").exists()
    assert (tmp_path / "artifacts" / "metrics.json").exists()


def test_high_risk_prediction(model_ready):
    result = predict_single(HIGH_RISK_RECORD, model_ready)
    assert result["risk_label"] in RISK_LABELS
    assert result["risk_label"] in ("High Risk", "Medium Risk"), (
        f"weak student should not be predicted Low Risk, got {result['risk_label']}"
    )
    probs = [result["prob_low"], result["prob_medium"], result["prob_high"]]
    assert abs(sum(probs) - 1.0) < 1e-3
    assert 0 < result["confidence"] <= 1
    assert result["recommendations"], "recommendations must be generated"
    assert result["model_version"]


def test_low_risk_prediction(model_ready):
    result = predict_single(LOW_RISK_RECORD, model_ready)
    assert result["risk_label"] in ("Low Risk", "Medium Risk")
    assert result["recommendations"]


def test_batch_prediction_handles_missing_values(model_ready):
    record = dict(HIGH_RISK_RECORD)
    record["attendance_pct"] = None
    record.pop("quiz_score")
    result = predict_records([record, LOW_RISK_RECORD], model_ready)
    assert len(result) == 2
    assert all(r["risk_label"] in RISK_LABELS for r in result)


def test_model_info_and_cache(model_ready):
    info = model_info(model_ready)
    assert info["model_name"]
    assert info["features"]
    # Cached load returns the same object.
    assert load_bundle(model_ready) is load_bundle(model_ready)


def test_missing_model_raises(tmp_path):
    with pytest.raises(ModelNotTrainedError):
        load_bundle(tmp_path / "nope.joblib")
