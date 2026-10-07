# EduRisk Predictor — System Documentation

Technical reference for developers and administrators. Companion to `README.md`
(quick start) and `docs/USER_MANUAL.md` (end-user guide).

---

## 1. Architecture

```
Browser (Bootstrap 5 + Chart.js, vendored)
   │  session cookie + CSRF token
   ▼
Flask application factory (app/__init__.py)
   ├── auth blueprint      login/logout, Flask-Login sessions
   ├── main blueprint      server-rendered pages (Jinja2)
   ├── api blueprint       JSON REST API (/api/*)
   ├── role decorator      admin | lecturer | advisor capabilities
   └── error handlers      HTML for browsers, JSON for API clients
   │
   ├── SQLAlchemy ORM ──── SQLite (dev) / MySQL (prod) via DATABASE_URL
   │      User · Student · Prediction · DatasetUpload · Intervention
   │
   └── ML service (app/ml)
          preprocess → train → evaluate → predict → recommend
                ▲                        │
                │                        ▼
        data/raw/student_records.csv   artifacts/model.joblib
                                        artifacts/metrics.json
                                        artifacts/plots/*.png
```

**Request lifecycle (score a student):** form/API → validation →
`_prepare_frame` (schema alignment, numeric coercion) → sklearn `Pipeline`
(imputer → scaler/one-hot → classifier) → `predict_proba` → risk label +
confidence → rule-based recommendations → response (and `Prediction` row if stored).

## 2. Data schema

| Table | Key columns |
| --- | --- |
| `users` | username (uniq), email (uniq), full_name, role, password_hash, is_active_flag |
| `students` | student_id (uniq), full_name, programme, department, gender, age, previous_gpa, attendance_pct, assignment_score, quiz_score, mid_sem_score, continuous_assessment, study_hours, exam_score, final_score, final_gpa, risk_level |
| `predictions` | student_id FK, risk_level (0/1/2), risk_label, confidence, prob_low/medium/high, recommendations (JSON), feature_snapshot (JSON), model_version, created_at |
| `dataset_uploads` | filename, user_id FK, row_count, accepted/rejected, status, message |
| `interventions` | student_id FK, advisor_id FK, prediction_id FK, action, notes, status, created_at |

Only **one row per student is considered current**: dashboards aggregate over
`MAX(id) GROUP BY student_id`.

### Feature schema (model contract)

Numeric (8): `age, previous_gpa, attendance_pct, assignment_score, quiz_score,
mid_sem_score, continuous_assessment, study_hours`
Categorical (3): `programme, department, gender`

Target: `risk_label` derived from `final_score` — **Low Risk ≥ 70**, **Medium Risk
50–69.99**, **High Risk < 50**. Outcome columns (`exam_score`, `final_score`,
`final_gpa`) are never model inputs (they don't exist before the examination).

Column aliases are normalised on import (`Attendance`→`attendance_pct`,
`CA`→`continuous_assessment`, `Matric No`→`student_id`, …).

## 3. Model card

| | |
| --- | --- |
| Algorithm | RandomForest (300 trees, `class_weight="balanced"`) inside a sklearn `Pipeline` |
| Selection | Best mean F1 across 5-fold stratified CV vs Decision Tree, Logistic Regression, Gaussian NB, RBF SVM (CalibratedClassifierCV) |
| Split | 80/20 stratified, `random_state=42` |
| Thresholds | see §2 (70 / 50 on the final score) |
| Artefacts | `artifacts/model.joblib` (pipeline + cohort stats + importances + version), `artifacts/metrics.json`, `artifacts/plots/*.png` |
| Acceptance | accuracy ≥ 0.70 (enforced by `scripts.setup`) |
| Refresh | `python -m scripts.setup --force-train`, `flask --app app train`, or **Retrain model** in the UI (admin) |

`model.joblib` bundles: pipeline, model name/version, feature lists, class order,
cohort mean/std per numeric feature (for explanations) and feature importances.
Loading is cached by file mtime; retraining invalidates the cache automatically.

### Explanation & recommendations

`explain_record` scores each numeric feature as
`global_importance × z-deficit` (how far the student is *below* the cohort mean) and
takes the top 3. `generate_recommendations` maps those factors to concrete advisor
actions, adds risk-band baseline advice, de-duplicates and caps at 5 items.

## 4. API notes

- Auth = session cookie (`POST /login`); API calls return `401 JSON` when anonymous.
- CSRF: send the token from `<meta name="csrf-token">` as `X-CSRFToken` on every
  write (Flask-WTF `CSRFProtect` guards both forms and API).
- Errors: `{ "error": "message" }` with 400/401/403/404/409/500.
- `GET /api/health` → 200 `{status:"ok"}` when DB reachable **and** model present,
  otherwise 503 `degraded` (use for container health checks).

## 5. Configuration & deployment

See `.env.example`. Important combinations:

```bash
# local development (defaults)
python run.py

# production with Waitress
FLASK_CONFIG=production SECRET_KEY=<long-random> python run.py --prod

# production with Gunicorn (Linux)
FLASK_CONFIG=production SECRET_KEY=<long-random> gunicorn -w 3 -b 0.0.0.0:8000 wsgi:app

# MySQL
DATABASE_URL=mysql+pymysql://user:pass@host:3306/academic_prediction
```

Docker: `docker compose up --build` (MySQL 8 + web, health-checked dependency).

## 6. Security controls

- Passwords hashed with Werkzeug **scrypt** (`generate_password_hash`).
- Session cookies `HttpOnly` + `SameSite=Lax`; `SECRET_KEY` enforced ≥16 chars in
  production (app refuses to boot otherwise).
- CSRF protection on every form and API write.
- Role-based access enforced server-side (templates only hide controls).
- Uploads: extension allow-list (CSV), size cap (`MAX_UPLOAD_MB`, default 5 MB),
  full validation before any DB write.
- Security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
  `Cache-Control: no-store` on API responses.
- SQL access only through the ORM; filenames sanitised by Flask's `send_from_directory`.

## 7. Testing

```bash
python -m pytest          # 51 tests
```

| File | Covers |
| --- | --- |
| `test_preprocess.py` | aliases, dedupe, imputation, range clamping, target bands, cohort stats |
| `test_ml.py` | model zoo, training ≥ 70% accuracy, artefacts/plots, inference, probabilities, missing values, cache |
| `test_api.py` | health, auth, summary, predict, upload flow, role enforcement, interventions, metrics, export |
| `test_web.py` | every page renders, forms validate, permissions redirect, plots served, 404 |

Configuration comes from `TestingConfig`: in-memory SQLite, CSRF disabled.

## 8. Operational notes

- **Retraining cadence:** once per semester (or after any bulk upload of outcomes).
  Commands: `python -m scripts.setup --force-train` or `flask --app app train`
  (or the **Retrain model** button in the UI, admin only).
- **Back up** `artifacts/` (model) and the database; both are required to reproduce
  predictions (`model_version` is stored on every prediction row).
- **Monitoring:** watch `/api/health`; check `metrics.json` accuracy after each
  retrain — drop below 0.70 means investigate data drift before trusting alerts.
- **Scaling:** the inference path is a single batched `predict_proba`; a few thousand
  students score in well under a second. For multi-instance deployments put MySQL in
  `DATABASE_URL` and run Gunicorn behind a reverse proxy with TLS.
