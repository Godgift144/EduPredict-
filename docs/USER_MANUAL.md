# EduRisk Predictor — User Manual

**Audience:** lecturers, academic advisors, administrators.
**Version:** 1.0

---

## 1. Logging in

1. Open the application URL (default `http://127.0.0.1:8000`).
2. Enter your username and password, then **Log in**.
   - Tick *Remember me* to stay signed in on a trusted device.
3. You land on your role's dashboard. The **left sidebar** shows only the pages
   your role can use, grouped as *Monitor · Work · Insights · Administration*;
   your avatar, role and the logout button sit at the bottom of the sidebar.

| Role | Dashboard | Sidebar pages |
| --- | --- | --- |
| **Lecturer** | *Early-warning dashboard* — risk cards, alerts, data-freshness panel | Students, Upload data, Predict, Reports, Model |
| **Academic Advisor** | *At-risk work-list* — priority queue, intervention coverage, status chart | Students, Predict, **Interventions**, Reports |
| **Administrator** | *Institutional overview* — institution-wide stats, system status | All pages, incl. Users and Interventions |

## 2. Reading the dashboard

- **Stat cards** — total students, high/medium/low risk counts, at-risk percentage,
  actual pass rate (once outcomes are loaded).
- **Risk distribution** — doughnut chart of the three risk bands.
- **Risk by department** — stacked bars for department-level comparisons.
- **Early-warning alerts** — the most recent high/medium-risk students; press **Open**
  to see the full record.
- Colors: 🟢 Low Risk · 🟡 Medium Risk · 🔴 High Risk.

## 3. Uploading student records (lecturer)

1. Go to **Upload data** and click **Download CSV template**.
2. Fill the template — required columns:
   `student_id, full_name, programme, department, gender, age, previous_gpa,
   attendance_pct, assignment_score, quiz_score, mid_sem_score,
   continuous_assessment, study_hours`
   (optional outcome columns: `exam_score, final_score, final_gpa`).
3. Choose the file, keep *Run predictions immediately after import* ticked, then
   **Upload and predict**.
4. The system reports how many rows were imported. Duplicates are removed, missing
   values imputed, out-of-range values corrected.
5. Review results on **Students** and the **Dashboard**.

Common upload errors:

| Message | Fix |
| --- | --- |
| `Missing required column(s): …` | Add the listed headers (spelling/spacing is normalised, e.g. `Attendance` works) |
| `Only .csv files are allowed` | Save the file as CSV |
| `The uploaded file is empty` | Re-export with data rows |

## 4. Predicting a single student

1. Open **Predict**.
2. Enter the mid-semester snapshot (previous GPA, attendance %, assignment, quiz,
   mid-semester and continuous-assessment scores, study hours).
3. Press **Predict performance** to get:
   - the **risk level** and **confidence**,
   - probability bars for each band,
   - the **key factors** driving the prediction,
   - **recommended interventions**.

Results appear only on screen; use **Upload data** if you want them stored permanently.

## 5. Working the at-risk list (advisor)

1. The **At-risk work-list** dashboard ranks the students who need support and
   shows how many still have *no intervention recorded*.
2. Open the **Interventions** page from the sidebar for the full workspace:
   the intervention log (filter by *Planned / In progress / Completed*) and the
   queue of at-risk students still uncovered.
3. Click **Start** (or **Counsel**) on a student to see:
   - the prediction, probabilities and key factors,
   - performance bars versus the cohort average,
   - the student record (actual scores when available).
4. Record what will be done in **Record an intervention** — type (counselling,
   mentoring, attendance follow-up, …), notes and status
   (*Planned → In progress → Completed*).
5. The intervention history stays on the student page for follow-up, and the
   coverage figures on the dashboard confirm cohort-level progress.

> Lecturers see the same alerts but no intervention controls — advising actions
> are recorded by advisors (and administrators).

## 6. Reports and exports

- **Reports** page: department table, programme chart, model summary, top at-risk list.
- **Export predictions (CSV)** — full risk list for meetings/analysis.
- **Print / PDF** — uses the browser's print dialog to produce a PDF.

## 7. Model page

Shows the deployed model (name, version, training date), the comparison of all five
algorithms (accuracy/precision/recall/F1/CV), per-class metrics, the confusion matrix,
feature importances and the dataset profile.

Administrators additionally get **Retrain model**, which re-runs training on the
current training CSV and re-scores every student.

## 8. Troubleshooting

| Symptom | What to do |
| --- | --- |
| "No trained model found" | Run `python -m scripts.setup` on the server |
| Redirected to login repeatedly | Session expired — log in again |
| "You do not have permission" | Your role lacks that capability; ask an administrator |
| Upload rejected as too large | Split the file or raise `MAX_UPLOAD_MB` |
| Dashboard shows zeros | Upload/score records first (or run `python -m scripts.setup`) |

## 9. Good practice

- Upload **once per semester milestone** (e.g. week 6) so predictions stay early.
- Never share accounts; passwords are stored hashed and cannot be recovered.
- Treat risk labels as **decision support** — combine them with your professional
  judgement and the student's circumstances.
- Follow your institution's data-protection policy when handling student records.
