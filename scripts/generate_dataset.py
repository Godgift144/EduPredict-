"""Deterministic synthetic student-records dataset generator.

Produces a realistic, reproducible CSV that mirrors the schema documented in
Chapter Three of the thesis: demographics, previous GPA, attendance,
assignments, quizzes, mid-semester and continuous-assessment scores, plus the
post-examination outcomes (exam score, final score, final GPA) used as ground
truth. Missing values and duplicate rows are injected on purpose so the
cleaning pipeline is exercised end-to-end.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42

PROGRAMMES = [
    "BSc Computer Science",
    "BSc Information Technology",
    "BSc Business Administration",
    "BSc Economics",
    "BSc Mathematics",
]

DEPARTMENTS = {
    "BSc Computer Science": "Computer Science",
    "BSc Information Technology": "Information Technology",
    "BSc Business Administration": "Business Administration",
    "BSc Economics": "Economics",
    "BSc Mathematics": "Mathematics",
}

FIRST_NAMES = [
    "Kwame", "Ama", "Kofi", "Abena", "Yaw", "Akosua", "Emmanuel", "Grace",
    "Daniel", "Sarah", "Michael", "Fatima", "Joseph", "Esther", "Peter",
    "Mary", "John", "Alice", "David", "Ruth", "Samuel", "Lydia", "Isaac",
    "Deborah", "Francis", "Comfort", "Elijah", "Priscilla", "Aaron", "Joyce",
    "Nathan", "Rebecca", "Victory", "Ibrahim", "Chidinma", "Obinna",
    "Tendai", "Chinwe", "Kemisola", "Bola",
]

LAST_NAMES = [
    "Mensah", "Owusu", "Asante", "Boateng", "Osei", "Addo", "Darko", "Amoah",
    "Nsiah", "Yeboah", "Agyeman", "Frimpong", "Antwi", "Sarpong", "Baidoo",
    "Kusi", "Anane", "Dapaah", "Oppong", "Bediako", "Ofori", "Larbi",
    "Danquah", "Iwu", "Adeyemi", "Olawale", "Nwosu", "Balogun", "Diallo",
    "Mwangi",
]


def generate(n: int = 2500, seed: int = SEED) -> pd.DataFrame:
    """Return a synthetic student dataset with realistic correlations."""
    rng = np.random.default_rng(seed)

    programme_idx = rng.integers(0, len(PROGRAMMES), size=n)
    programmes = [PROGRAMMES[i] for i in programme_idx]
    departments = [DEPARTMENTS[p] for p in programmes]

    # Latent academic ability drives every observable feature.
    ability = rng.normal(0.0, 1.0, size=n)
    effort = rng.normal(0.0, 0.7, size=n)

    study_hours = np.clip(9.0 + 3.0 * ability + 2.0 * effort + rng.normal(0, 2.5, n), 0, 45)
    previous_gpa = np.clip(2.65 + 0.55 * ability + 0.30 * effort + rng.normal(0, 0.30, n), 0.0, 4.0)
    attendance = np.clip(76 + 8.0 * ability + 4.0 * effort + rng.normal(0, 6.0, n), 15, 100)
    assignment = np.clip(62 + 8.0 * ability + 0.5 * study_hours + rng.normal(0, 7.0, n), 0, 100)
    quiz = np.clip(57 + 9.0 * ability + 0.5 * study_hours + rng.normal(0, 8.0, n), 0, 100)
    mid_sem = np.clip(58 + 9.0 * ability + 0.3 * study_hours + 0.10 * attendance + rng.normal(0, 7.0, n), 0, 100)
    ca = np.clip(0.4 * assignment + 0.3 * quiz + 0.3 * mid_sem + rng.normal(0, 2.5, n), 0, 100)

    exam = np.clip(
        54
        + 11.0 * ability
        + 0.35 * study_hours
        + 0.10 * attendance
        + 1.5 * (previous_gpa - 2.65)
        + rng.normal(0, 5.0, n),
        0,
        100,
    )
    final_score = np.clip(0.7 * exam + 0.3 * ca, 0, 100)
    final_gpa = np.clip(((final_score - 40.0) / 60.0) * 4.0, 0.0, 4.0)

    age = np.clip(rng.normal(21.5, 2.6, n).round().astype(int), 17, 35)
    gender = rng.choice(["Male", "Female", "Other"], size=n, p=[0.5, 0.47, 0.03])

    student_ids = [f"STU{i + 1:05d}" for i in range(n)]
    names = [
        f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}" for _ in range(n)
    ]

    df = pd.DataFrame(
        {
            "student_id": student_ids,
            "full_name": names,
            "programme": programmes,
            "department": departments,
            "gender": gender,
            "age": age,
            "previous_gpa": np.round(previous_gpa, 2),
            "attendance_pct": np.round(attendance, 1),
            "assignment_score": np.round(assignment, 1),
            "quiz_score": np.round(quiz, 1),
            "mid_sem_score": np.round(mid_sem, 1),
            "continuous_assessment": np.round(ca, 1),
            "study_hours": np.round(study_hours, 1),
            "exam_score": np.round(exam, 1),
            "final_score": np.round(final_score, 1),
            "final_gpa": np.round(final_gpa, 2),
        }
    )

    # ---- realistic data-quality issues ---------------------------------- #
    numeric_missing = [
        "previous_gpa", "attendance_pct", "assignment_score", "quiz_score",
        "mid_sem_score", "continuous_assessment", "study_hours", "age",
    ]
    for col in numeric_missing:
        mask = rng.random(n) < 0.03
        df.loc[mask, col] = np.nan
    cat_missing = rng.random(n) < 0.02
    df.loc[cat_missing, "programme"] = np.nan
    df.loc[cat_missing, "department"] = np.nan

    # ~2% duplicate rows, as often seen in hand-maintained exports.
    dup_count = max(int(n * 0.02), 1)
    dupes = df.sample(n=dup_count, random_state=seed)
    df = pd.concat([df, dupes], ignore_index=True)
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df


def main() -> None:  # pragma: no cover - CLI entry point
    parser = argparse.ArgumentParser(description="Generate the synthetic dataset.")
    parser.add_argument("--rows", type=int, default=2500)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out", default=None, help="Output CSV path")
    args = parser.parse_args()

    out = Path(args.out) if args.out else (
        Path(__file__).resolve().parent.parent / "data" / "raw" / "student_records.csv"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    frame = generate(args.rows, args.seed)
    frame.to_csv(out, index=False)
    print(f"Wrote {len(frame)} rows to {out}")


if __name__ == "__main__":
    main()
