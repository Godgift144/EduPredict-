"""Model training: comparison, cross-validation, artefact & plot generation.

The training entry point is :func:`train_experiment`, which:

1. loads and cleans the dataset,
2. derives the risk-level target from the final outcome,
3. performs a stratified train/test split,
4. compares five classifiers with 5-fold stratified cross-validation,
5. fits the best model, evaluates it on the held-out test set,
6. persists ``model.joblib`` + ``metrics.json`` and renders report plots.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.calibration import CalibratedClassifierCV  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.model_selection import (  # noqa: E402
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.naive_bayes import GaussianNB  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.svm import SVC  # noqa: E402
from sklearn.tree import DecisionTreeClassifier  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402

from .evaluate import evaluate_predictions  # noqa: E402
from .preprocess import (  # noqa: E402
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    RISK_LABELS,
    build_preprocessor,
    clean_dataset,
    cohort_statistics,
    derive_target,
)

MODEL_VERSION_FMT = "%Y%m%d-%H%M%S"


def build_model_zoo(random_state: int = 42) -> dict[str, Pipeline]:
    """Classifiers compared during training (per the methodology chapter)."""
    return {
        "Random Forest": Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=300,
                        class_weight="balanced",
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "Decision Tree": Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                (
                    "classifier",
                    DecisionTreeClassifier(
                        class_weight="balanced", random_state=random_state
                    ),
                ),
            ]
        ),
        "Logistic Regression": Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=2000, class_weight="balanced", random_state=random_state
                    ),
                ),
            ]
        ),
        "Naive Bayes": Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                ("classifier", GaussianNB()),
            ]
        ),
        "Support Vector Machine": Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                (
                    "classifier",
                    CalibratedClassifierCV(
                        SVC(
                            kernel="rbf",
                            C=1.0,
                            gamma="scale",
                            class_weight="balanced",
                            random_state=random_state,
                        ),
                        ensemble=False,
                    ),
                ),
            ]
        ),
    }


def _feature_names(pipeline: Pipeline) -> list[str]:
    """Human-readable names for the transformed feature matrix."""
    pre = pipeline.named_steps["preprocess"]
    names = list(pre.get_feature_names_out())
    cleaned = []
    for name in names:
        if "__" in name:
            prefix, rest = name.split("__", 1)
            if prefix == "num":
                cleaned.append(rest)
            else:  # cat__programme_Computer Science -> programme: Computer Science
                if "_" in rest:
                    feat, value = rest.split("_", 1)
                    cleaned.append(f"{feat}: {value}")
                else:
                    cleaned.append(rest)
        else:
            cleaned.append(name)
    return cleaned


def _extract_importances(pipeline: Pipeline) -> list[float] | None:
    clf = pipeline.named_steps["classifier"]
    if hasattr(clf, "feature_importances_"):
        return [float(v) for v in clf.feature_importances_]
    if hasattr(clf, "coef_"):
        coef = np.asarray(clf.coef_)
        return [float(v) for v in np.mean(np.abs(coef), axis=0)]
    return None


# --------------------------------------------------------------------------- #
# Plots
# --------------------------------------------------------------------------- #
def plot_class_distribution(y: pd.Series, path: Path) -> None:
    counts = y.value_counts().reindex(RISK_LABELS, fill_value=0)
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = {"Low Risk": "#2e7d32", "Medium Risk": "#f9a825", "High Risk": "#c62828"}
    ax.bar(counts.index, counts.values, color=[colors[i] for i in counts.index])
    ax.set_title("Distribution of Academic Risk Levels")
    ax.set_xlabel("Risk level")
    ax.set_ylabel("Number of students")
    for x, v in zip(counts.index, counts.values):
        ax.text(x, v + 5, str(v), ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_model_comparison(results: dict, path: Path) -> None:
    names = list(results.keys())
    acc = [results[n]["test"]["accuracy"] for n in names]
    f1 = [results[n]["test"]["f1_weighted"] for n in names]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - 0.2, acc, width=0.4, label="Accuracy", color="#1976d2")
    ax.bar(x + 0.2, f1, width=0.4, label="F1 (weighted)", color="#7b1fa2")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_title("Model Comparison on the Held-out Test Set")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_confusion_matrix(metrics: dict, path: Path, title: str) -> None:
    cm = np.asarray(metrics["confusion_matrix"])
    labels = metrics["labels"]
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels, rotation=20, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_feature_importance(names: list[str], values: list[float], path: Path) -> None:
    pairs = sorted(zip(names, values), key=lambda kv: kv[1], reverse=True)[:15]
    pairs = pairs[::-1]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh([p[0] for p in pairs], [p[1] for p in pairs], color="#1976d2")
    ax.set_title("Top 15 Feature Importances (best model)")
    ax.set_xlabel("Importance")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Training experiment
# --------------------------------------------------------------------------- #
def train_experiment(
    csv_path: str | Path,
    artifacts_dir: str | Path,
    *,
    test_size: float = 0.2,
    random_state: int = 42,
    verbose: bool = False,
) -> dict:
    """Run the full training experiment and persist artefacts.

    Returns the summary dictionary that is also written to
    ``<artifacts_dir>/metrics.json``.
    """
    csv_path = Path(csv_path)
    artifacts_dir = Path(artifacts_dir)
    plots_dir = artifacts_dir / "plots"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(csv_path)
    n_raw = len(raw)

    df = clean_dataset(raw, require_target=True)
    df = derive_target(df) if "risk_label" not in df.columns else df

    X = df[FEATURE_COLUMNS]
    y = df["risk_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    results: dict[str, dict] = {}
    fitted: dict[str, Pipeline] = {}
    for name, pipeline in build_model_zoo(random_state).items():
        started = time.perf_counter()
        cv = cross_val_score(
            pipeline,
            X_train,
            y_train,
            cv=StratifiedKFold(5, shuffle=True, random_state=random_state),
            scoring="f1_weighted",
            n_jobs=-1,
        )
        pipeline.fit(X_train, y_train)
        elapsed = time.perf_counter() - started
        y_pred = pipeline.predict(X_test)
        metrics = evaluate_predictions(y_test, y_pred)
        results[name] = {
            "cv_f1_mean": round(float(cv.mean()), 4),
            "cv_f1_std": round(float(cv.std()), 4),
            "train_seconds": round(elapsed, 3),
            "test": metrics,
        }
        fitted[name] = pipeline
        if verbose:
            print(
                f"  {name:24s} acc={metrics['accuracy']:.3f} "
                f"f1={metrics['f1_weighted']:.3f} cv={cv.mean():.3f}±{cv.std():.3f}"
            )

    # Select the best model by cross-validated F1 (ties -> test accuracy).
    best_name = max(
        results,
        key=lambda n: (results[n]["cv_f1_mean"], results[n]["test"]["accuracy"]),
    )
    best_pipeline = fitted[best_name]
    best_metrics = results[best_name]["test"]

    model_version = datetime.now(timezone.utc).strftime(MODEL_VERSION_FMT)
    feature_names = _feature_names(best_pipeline)
    importances = _extract_importances(best_pipeline)

    bundle = {
        "pipeline": best_pipeline,
        "model_name": best_name,
        "model_version": model_version,
        "feature_columns": FEATURE_COLUMNS,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "risk_labels": RISK_LABELS,
        "cohort_stats": cohort_statistics(df),
        "feature_names": feature_names,
        "feature_importances": importances,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_rows": int(len(df)),
        "raw_rows": int(n_raw),
    }
    model_path = artifacts_dir / "model.joblib"
    joblib.dump(bundle, model_path)

    summary = {
        "model_version": model_version,
        "model_name": best_name,
        "trained_at": bundle["trained_at"],
        "dataset": {
            "path": str(csv_path),
            "raw_rows": int(n_raw),
            "rows_used": int(len(df)),
            "dropped_rows": int(n_raw - len(df)),
            "features": FEATURE_COLUMNS,
            "target": "risk_label",
            "class_distribution": {
                k: int(v) for k, v in y.value_counts().reindex(RISK_LABELS, fill_value=0).items()
            },
        },
        "split": {"test_size": test_size, "random_state": random_state,
                  "train_rows": int(len(X_train)), "test_rows": int(len(X_test))},
        "models": results,
        "best_model": best_name,
        "best_metrics": best_metrics,
        "feature_importances": (
            [
                {"feature": f, "importance": round(float(v), 5)}
                for f, v in sorted(
                    zip(feature_names, importances), key=lambda kv: kv[1], reverse=True
                )
            ]
            if importances
            else []
        ),
    }

    metrics_path = artifacts_dir / "metrics.json"
    metrics_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # ---- plots -------------------------------------------------------- #
    plot_class_distribution(y, plots_dir / "class_distribution.png")
    plot_model_comparison(results, plots_dir / "model_comparison.png")
    plot_confusion_matrix(
        best_metrics,
        plots_dir / "confusion_matrix.png",
        f"Confusion Matrix — {best_name}",
    )
    if importances:
        plot_feature_importance(
            feature_names, importances, plots_dir / "feature_importance.png"
        )

    return summary


if __name__ == "__main__":  # pragma: no cover
    import argparse

    from ..config import ARTIFACTS_DIR, TRAINING_DATA_PATH

    parser = argparse.ArgumentParser(description="Train the risk-prediction model.")
    parser.add_argument("--data", default=TRAINING_DATA_PATH)
    parser.add_argument("--artifacts", default=ARTIFACTS_DIR)
    args = parser.parse_args()
    summary = train_experiment(args.data, args.artifacts, verbose=True)
    print(f"\nBest model: {summary['best_model']} "
          f"(accuracy={summary['best_metrics']['accuracy']:.3f})")
