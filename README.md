# EduRisk Predictor

**An AI-based system for predicting university students' academic performance and
assisting lecturers and academic advisors in identifying at-risk students early.**

The system ingests mid-semester student records (attendance, assignments, quizzes,
continuous assessment, previous GPA, study hours, demographics), scores every student
with a Random Forest classifier into **Low Risk / Medium Risk / High Risk** bands, and
presents the results through lecturer and academic-advisor dashboards with
rule-based early-intervention recommendations.

---

## Features

| Deliverable | Where |
| --- | --- |
| Machine-learning prediction model (Random Forest, compared against Decision Tree, Logistic Regression, Naïve Bayes and SVM) | `app/ml/` |
| AI-based web application (Flask + Bootstrap) | `app/` |
| Lecturer dashboard (risk distribution, early-warning alerts, data freshness) | `/dashboard`, `/upload` |
| Academic-advisor dashboard (priority queue + intervention workspace) | `/dashboard`, `/interventions`, `/students/<id>` |
| Single-student prediction form | `/predict` |
| Student performance & risk prediction reports (CSV export, printable) | `/reports`, `/reports/export.csv` |
| Model performance report (accuracy, precision, recall, F1, confusion matrix, feature importance) | `/model` |
| REST JSON API | `/api/*` (see below) |
| Role-based access control (admin / lecturer / advisor), CSRF, hashed passwords | `app/auth`, `app/decorators.py` |
| Test suite (51 tests: preprocessing, ML, API, web UI, role workspaces) | `tests/` |

## Tech stack

- **Language:** Python 3.12+ (developed on 3.14)
- **Web framework:** Flask 3 + Flask-Login + Flask-WTF (CSRF) + Flask-SQLAlchemy
- **ML:** scikit-learn, pandas, NumPy, joblib; plots via Matplotlib
- **Database:** SQLite by default (zero-config development), **MySQL** for production
  via `DATABASE_URL` (SQLAlchemy ORM — no code changes needed)
- **Frontend:** Bootstrap 5 + Chart.js (vendored locally, no CDN dependency)
- **Server:** Waitress (Windows/local) or Gunicorn (Docker/Linux)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

python -m scripts.setup             # generate data → train model → seed DB

python run.py                       # http://127.0.0.1:8000
```

Demo accounts (development seed):

| Role | Username | Password |
| --- | --- | --- |
| Administrator | `admin` | `Admin@12345` |
| Lecturer | `lecturer` | `Lecturer@1234` |
| Academic Advisor | `advisor` | `Advisor@1234` |

> Change these before any real deployment (`SEED_*_PASSWORD` env vars, or create fresh
> users on the **Users** page).

## Commands

| Command | Purpose |
| --- | --- |
| `python -m scripts.setup` | One-shot bootstrap (dataset → model → seeded database) |
| `python -m scripts.setup --force-train` | Retrain the model |
| `python -m scripts.setup --rows 5000` | Generate a larger synthetic dataset |
| `python -m scripts.train` | Train only (`--data`, `--artifacts`, `--test-size`, `--seed`) |
| `python -m scripts.generate_dataset` | Regenerate `data/raw/student_records.csv` |
| `flask --app app init-db` / `flask --app app train` / `flask --app app seed` | Same operations via Flask CLI |
| `python -m pytest` | Run the test suite |
| `python run.py --prod` | Serve with Waitress (production WSGI) |

## Configuration

Copy `.env.example` → `.env`:

| Variable | Meaning |
| --- | --- |
| `FLASK_CONFIG` | `development` \| `testing` \| `production` |
| `SECRET_KEY` | Session signing key (**required**, ≥16 chars in production) |
| `DATABASE_URL` | `sqlite:///data/app.db` or `mysql+pymysql://user:pass@host/db` |
| `MAX_UPLOAD_MB` | Upload size limit (default 5 MB) |
| `PORT` | Server port (default 8000) |

### Production (Docker + MySQL)

```bash
docker compose up --build      # web on :8000, MySQL 8 with health check
```

The image trains the model during build if `artifacts/model.joblib` is absent.
Set a strong `SECRET_KEY` and MySQL credentials in `docker-compose.yml` before use.

## System workflow

```
Student records (CSV upload / single form)
        │
        ▼
Data cleaning ── dedupe · type coercion · range checks · median/mode imputation
        │
        ▼
Feature extraction ── 8 numeric + 3 categorical features (pre-exam snapshot)
        │
        ▼
Random Forest model ── calibrated class probabilities
        │
        ├── Low Risk   → monitor / enrichment
        ├── Medium Risk → watch-list, peer tutorials
        └── High Risk  → advisor alert
                │
                ▼
        Intervention recorded → follow-up tracked on the student page
```

## REST API

All endpoints require an authenticated session (`POST /login` first) and writes
require the `X-CSRFToken` header (token from the `<meta name="csrf-token">` tag).

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Liveness/readiness (DB + model state) |
| GET | `/api/summary` | Risk counts, department/programme distributions |
| GET | `/api/alerts?limit=20` | Recent medium/high-risk students |
| GET | `/api/students?q=&risk=&department=&page=` | Paginated, filterable students |
| GET | `/api/students/<id>` | Student + prediction + interventions |
| POST | `/api/predict` | Score one JSON record |
| POST | `/api/upload` | Upload a CSV (multipart) and score it |
| POST | `/api/students/<id>/interventions` | Record an intervention (advisor/admin) |
| GET | `/api/model/info`, `/api/model/metrics` | Deployed-model metadata & full metrics |
| POST | `/api/model/retrain` | Retrain from the training CSV (admin) |
| GET | `/api/reports/predictions.csv` | Export the prediction report |

## Project layout

```
app/
  __init__.py        application factory (config, extensions, CLI, security headers)
  config.py          development / testing / production configuration
  extensions.py      SQLAlchemy, Flask-Login, CSRF
  models.py          User, Student, Prediction, DatasetUpload, Intervention
  forms.py           WTForms (CSRF-protected)
  decorators.py      role-based access control
  auth/              login / logout
  main/              dashboard, students, upload, predict, reports, model, users
  api/               JSON REST API
  ml/                preprocess · train · evaluate · predict (+ recommendations)
  services/          data ingestion, prediction persistence, report aggregations
  templates/         Jinja2 + Bootstrap 5
  static/            vendored Bootstrap/Chart.js, CSS, JS
scripts/             setup · generate_dataset · train (CLI entry points)
tests/               51 tests: preprocessing, ML, API, web UI, role workspaces
artifacts/           model.joblib, metrics.json, plots/
data/raw/            training dataset + CSV upload template
docs/                user manual and system documentation
```

## Documentation

- [`docs/USER_MANUAL.md`](docs/USER_MANUAL.md) — step-by-step guide for lecturers/advisors
- [`docs/SYSTEM_DOCUMENTATION.md`](docs/SYSTEM_DOCUMENTATION.md) — architecture, data schema, model card, API, deployment, security
- [`Thesis_Report.md`](Thesis_Report.md) — full thesis report following the university template

## Data ethics & limitations

Predictions are decision **support**, not decisions: they must be reviewed by lecturers
and advisors alongside professional judgement. Student data is access-controlled,
hashed passwords only, and should be processed under the institution's data-protection
policy. Model quality depends on data quality — retrain each semester with fresh,
authorized records.
