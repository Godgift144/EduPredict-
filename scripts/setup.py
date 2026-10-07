"""One-shot project bootstrap: ``python -m scripts.setup``.

Steps:
  1. create required directories
  2. generate the dataset (if missing)
  3. train the model (if missing, or with --force-train)
  4. create database tables
  5. seed demo users, students and predictions (if empty)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the project.")
    parser.add_argument("--rows", type=int, default=2500, help="Synthetic dataset size")
    parser.add_argument("--force-train", action="store_true", help="Retrain the model")
    parser.add_argument("--skip-seed", action="store_true", help="Skip database seeding")
    args = parser.parse_args()

    from app import create_app
    from app.config import ARTIFACTS_DIR, MODEL_PATH, RAW_DATA_DIR, TRAINING_DATA_PATH

    for path in (RAW_DATA_DIR, ARTIFACTS_DIR, ARTIFACTS_DIR / "plots",
                 ROOT / "data" / "uploads"):
        path.mkdir(parents=True, exist_ok=True)

    # 1. Dataset --------------------------------------------------------- #
    if not os.path.exists(TRAINING_DATA_PATH):
        print("==> Generating synthetic dataset ...")
        from scripts.generate_dataset import generate

        frame = generate(args.rows)
        frame.to_csv(TRAINING_DATA_PATH, index=False)
        print(f"    {len(frame)} rows -> {TRAINING_DATA_PATH}")
    else:
        print(f"==> Dataset already present: {TRAINING_DATA_PATH}")

    # 2. Model ----------------------------------------------------------- #
    if args.force_train or not os.path.exists(MODEL_PATH):
        print("==> Training models ...")
        from app.ml.train import train_experiment

        summary = train_experiment(TRAINING_DATA_PATH, ARTIFACTS_DIR, verbose=True)
        metrics = summary["best_metrics"]
        print(
            f"    Best: {summary['best_model']}  "
            f"acc={metrics['accuracy']:.4f} f1={metrics['f1_weighted']:.4f}"
        )
        if metrics["accuracy"] < 0.70:
            print("    WARNING: accuracy below the 0.70 acceptance threshold.")
    else:
        print("==> Model already trained (use --force-train to retrain)")

    # 3 & 4. Database + seed -------------------------------------------- #
    app = create_app(os.environ.get("FLASK_CONFIG", "development"))
    with app.app_context():
        from app.extensions import db
        from app.seed import seed_database

        db.create_all()
        if args.skip_seed:
            print("==> Seeding skipped")
        else:
            print("==> Seeding database ...")
            stats = seed_database()
            print(f"    {stats}")

    print("\nSetup complete. Start the app with:  python run.py")
    print("Demo accounts: admin/Admin@12345, lecturer/Lecturer@1234, advisor/Advisor@1234")


if __name__ == "__main__":
    main()
