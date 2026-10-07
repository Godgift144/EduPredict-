"""Train the risk-prediction model: ``python -m scripts.train``."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys

sys.path.insert(0, str(ROOT))

from app.config import ARTIFACTS_DIR, TRAINING_DATA_PATH  # noqa: E402
from app.ml.train import train_experiment  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the prediction model.")
    parser.add_argument("--data", default=TRAINING_DATA_PATH)
    parser.add_argument("--artifacts", default=str(ARTIFACTS_DIR))
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"Training on {args.data} ...")
    summary = train_experiment(
        args.data,
        args.artifacts,
        test_size=args.test_size,
        random_state=args.seed,
        verbose=True,
    )
    best = summary["best_model"]
    metrics = summary["best_metrics"]
    print(
        f"\nBest model: {best}\n"
        f"  accuracy  = {metrics['accuracy']:.4f}\n"
        f"  precision = {metrics['precision_weighted']:.4f}\n"
        f"  recall    = {metrics['recall_weighted']:.4f}\n"
        f"  f1        = {metrics['f1_weighted']:.4f}\n"
        f"  artefacts -> {args.artifacts}"
    )


if __name__ == "__main__":
    main()
