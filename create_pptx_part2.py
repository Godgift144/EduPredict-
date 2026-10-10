# Part 2: polished build
page = 0
def nxt():
    global page
    page += 1
    return page

# =====================================================================
# FRONT MATTER  (1..9)
# =====================================================================
s = add_slide(); slide_title(s, nxt())                      # 1
s = add_slide(); slide_declaration(s, nxt())                # 2
s = add_slide(); slide_abstract(s, nxt())                   # 3
s = add_slide(); slide_dedication(s, nxt())                 # 4
s = add_slide(); slide_acknowledgement(s, nxt())            # 5
s = add_slide(); slide_toc(s, nxt())                        # 6
s = add_slide(); slide_lof(s, nxt())                        # 7
s = add_slide(); slide_lot(s, nxt())                        # 8
s = add_slide(); slide_loa(s, nxt())                        # 9

# =====================================================================
# CHAPTER ONE  (10..11)
# =====================================================================
# 10: 1.1 + 1.2  (Background & Motivation, Statement of Problem)
bullets_10 = [
    "1.1  Background and Motivation",
    "The advancement of Artificial Intelligence has transformed many sectors including healthcare, finance, transportation and education (Holmes et al., 2019).",
    "In higher education, universities generate large volumes of student data: examination scores, attendance records, assignment marks, continuous-assessment scores, LMS activity and demographic information.",
    "Despite the availability of these data, many institutions still rely on traditional methods of identifying academically struggling students \u2014 typically only after poor examination results or a low GPA has accumulated.",
    "Early identification is important because it enables lecturers and academic advisors to provide timely academic support, counselling, mentoring and intervention strategies.",
    "Delayed identification limits effectiveness: educators have little time to assist students before performance deteriorates further.",
    "Conventional monitoring is largely manual, time-consuming and dependent on individual observation; it may overlook subtle indicators of academic risk hidden within student records (Romero & Ventura, 2010).",
    "1.2  Statement of the Problem",
    "Many universities identify academically weak students only after they have performed poorly in examinations or accumulated low GPAs.",
    "This delayed identification limits the effectiveness of interventions \u2014 lecturers and advisors have little time to assist before academic performance deteriorates further.",
    "Current methods of monitoring student performance are largely manual, time-consuming and dependent on lecturers\u2019 individual observations.",
    "Existing Student Information Systems store student records but rarely provide predictive capability.",
    "Where predictions exist, they commonly focus only on final GPA, lack visual dashboards, do not generate early-intervention alerts and are not designed for local university environments.",
    "Consequently, lecturers and advisors must interpret raw spreadsheets themselves, and no systematic link exists between a prediction and the intervention it should trigger.",
    "There is a need for an intelligent system capable of predicting underperformance BEFORE final examinations, so that timely interventions can be implemented.",
]
s = add_slide()
section_group_slide(s, 1, "INTRODUCTION", ["1.1  |  1.2"], bullets_10, nxt(),
                    note="Early identification enables timely support; delayed discovery comes too late to help.",
                    accent=BLUE)

# 11: 1.3 + 1.4 + 1.5 + 1.6
bullets_11 = [
    "1.3  Scope of the Study",
    "Predicts academic performance from pre-final-exam data: CA scores, attendance, previous GPA, assignment, quiz, mid-semester, study hours, programme, department, age, gender.",
    "Outputs three academic risk levels: Low Risk (\u226570), Medium Risk (50\u201369.99), High Risk (<50).",
    "Develops a prototype for university use; does NOT replace lecturers\u2019 professional judgement \u2014 decision support that prioritises who to attend to first.",
    "Covers system design, data collection & preprocessing, model development & evaluation, web app implementation and testing.",
    "SIS integration, longitudinal multi-cohort tracking and formal large-sample user studies are outside the current scope.",
    "1.4  Research Objectives",
    "Global objective: develop an AI-based system that predicts university students\u2019 academic performance and assists lecturers and academic advisors in identifying at-risk students at an early stage.",
    "Specific objectives: (1) design the system; (2) collect & preprocess data; (3) develop an ML model; (4) classify risk levels; (5) build a web dashboard; (6) provide intervention recommendations; (7) evaluate accuracy & effectiveness.",
    "1.5  Research Contribution",
    "Students: early identification of learning difficulties, improved academic support and better academic planning.",
    "Lecturers: easier monitoring and early detection of struggling students without manual spreadsheet analysis.",
    "Academic Advisors: better decision-making through a prioritised at-risk work-list and improved, evidence-informed student counselling, with interventions recorded & tracked.",
    "University Management: reduced dropout rates, improved graduation rates and better educational planning informed by institution-wide risk statistics.",
    "Researchers: a working reference implementation (preprocessing pipeline, trained model, evaluation harness and dashboards) for future AI applications in education.",
    "Unlike studies that stop at reporting model accuracy, this project delivers an end-to-end operational system coupling prediction with dashboards, alerts, intervention recommendations and intervention tracking.",
    "1.6  Organization of the Study",
    "Five chapters: Ch1 introduces the study; Ch2 reviews literature; Ch3 presents methodology; Ch4 covers experimental results & discussions; Ch5 presents conclusions, findings, recommendations, limitations and future work.",
]
s = add_slide()
section_group_slide(s, 1, "INTRODUCTION", ["1.3  |  1.4  |  1.5  |  1.6"], bullets_11, nxt(),
                    accent=BLUE)

# =====================================================================
# CHAPTER TWO  (12..13)
# =====================================================================
bullets_12 = [
    "2.1  Introduction",
    "This chapter reviews previous studies on Artificial Intelligence, Machine Learning, Educational Data Mining, Learning Analytics and academic performance prediction systems.",
    "It establishes the theoretical foundation of the study, summarises approaches reported in the literature, identifies existing systems and their limitations, and locates the research gap this project addresses.",
    "2.2  Artificial Intelligence in Education",
    "Artificial Intelligence refers to computer systems capable of performing tasks that normally require human intelligence, such as learning, reasoning, prediction and decision-making (Bishop, 2006).",
    "AI has been applied in education for several decades, from intelligent tutoring systems to automated assessment and institutional analytics.",
    "Holmes et al. (2019) describe AI in education as encompassing systems that adapt to learners, support teachers with data-driven insight and inform policy.",
    "Luckin et al. (2016) argue that the value of AI in education lies in augmenting educators\u2019 judgement rather than replacing it.",
    "Zawacki-Richter et al. (2019), in a systematic review of AI applications in higher education, identify four application areas: (1) learner modelling & profiling; (2) intelligent tutoring & recommendation; (3) assessment & feedback; (4) administration & retention analytics.",
    "Student performance prediction belongs to the fourth area and is among the most widely deployed.",
]
s = add_slide()
section_group_slide(s, 2, "LITERATURE REVIEW", ["2.1  |  2.2"], bullets_12, nxt(), accent=BLUE)

bullets_13 = [
    "2.3  Machine Learning",
    "Machine Learning is a branch of AI in which computers learn patterns from historical data rather than following explicitly programmed rules (James et al., 2013).",
    "Given past student records with known outcomes, an ML algorithm learns a mapping from input features (attendance, assessments, prior attainment) to an output (future performance band), which can then be applied to new, unseen students.",
    "Common algorithms in educational prediction:",
    "\u2022  Decision Tree \u2014 interpretable rule-like splits, but prone to overfitting;",
    "\u2022  Random Forest \u2014 ensemble of decision trees (Breiman, 2001), generally accurate and robust;",
    "\u2022  Logistic Regression \u2014 a linear probabilistic baseline, fast and interpretable;",
    "\u2022  Na\u00EFve Bayes \u2014 probabilistic classifier effective with small data (Kotsiantis et al., 2004);",
    "\u2022  Support Vector Machine (SVM) \u2014 maximum-margin classification effective in high-dimensional spaces (Vapnik, 1998);",
    "\u2022  Neural Networks \u2014 non-linear models capturing complex interactions at the cost of data and tuning.",
    "Random Forest is selected as primary: performs well on educational tabular data, handles many features, resists overfitting via bagging, supports class weighting for imbalanced bands, and provides feature-importance for explainability (Breiman, 2001; Scikit-learn, Pedregosa et al., 2011).",
    "2.4  Educational Data Mining",
    "EDM extracts useful knowledge from educational datasets using statistical, machine-learning and visualisation techniques (Romero & Ventura, 2010; Romero et al., 2010).",
    "Typical student data: attendance; assignment scores; quiz scores; continuous assessment; previous GPA; examination scores; course registration; demographic information.",
    "Romero and Ventura (2010) taxonomise EDM tasks as prediction, clustering, relationship mining, distillation and discovery with visualisation.",
    "Student performance prediction is a prediction task: the target is typically course completion, final grade or GPA.",
    "Early studies used Na\u00EFve Bayes on distance-learning data (Kotsiantis et al., 2004); ensemble methods such as Random Forest frequently outperform single learners on tabular educational data while remaining interpretable through feature importance (Larose, 2014).",
    "Recurring finding: performance is multi-factorial \u2014 prior attainment, assessment engagement and attendance are consistently among the strongest predictors; demographic variables contribute comparatively little (Romero & Ventura, 2010).",
    "2.5  Learning Analytics",
    "Learning Analytics involves collecting, measuring, analysing and reporting data about learners and their contexts to understand and optimise learning (Siemens & Long, 2011).",
    "Reported benefits: early intervention; personalised learning; improved retention; better decision-making.",
    "Pena-Ayala (2014): most effective when predictions are embedded in the workflow of those who act on them \u2014 dashboards, alerts and recommendations \u2014 rather than delivered as standalone statistics.",
    "This design principle directly shapes the present project: predictions are surfaced on role-specific dashboards, ranked alerts and per-student recommendation lists, and each prediction can be converted into a tracked intervention record.",
    "2.6  Existing Systems",
    "Many universities use Student Information Systems (SIS) that store student records but lack predictive capability.",
    "Existing AI systems mainly focus on: dropout prediction; GPA prediction; course recommendation.",
    "Commercial early-alert modules of learning-management systems provide threshold-based alerts (e.g. grade below a cut-off or attendance below a percentage) but these are simple rules rather than learned models.",
    "They rarely combine multiple weak indicators into a single calibrated risk probability (Siemens & Long, 2011).",
    "Few systems integrate prediction with advisor dashboards and intervention recommendations; fewer still record what intervention was actually delivered, closing no feedback loop for the institution.",
    "2.7  Research Gap",
    "Most existing systems exhibit these shortcomings:",
    "   1.  No early-intervention alerts tied to concrete recommended actions.",
    "   2.  Focus only on final GPA prediction rather than actionable risk bands before examinations.",
    "   3.  No visual dashboards designed for lecturers and advisors.",
    "   4.  Not designed for local university environments and their data conventions.",
    "   5.  Seldom track whether predicted at-risk students received and completed interventions.",
    "This project closes the gap: calibrated three-level risk classification from mid-semester data, role-based dashboards with early-warning alerts, rule-based intervention recommendations, and an auditable intervention record per student.",
    "The complete system \u2014 model, ingestion pipeline, dashboards, API and reporting \u2014 is implemented and evaluated in the following chapters.",
]
s = add_slide()
section_group_slide(s, 2, "LITERATURE REVIEW", ["2.3  |  2.4  |  2.5  |  2.6  |  2.7"], bullets_13, nxt(),
                    accent=GOLD)

# =====================================================================
# CHAPTER THREE  (14..17)
# =====================================================================
bullets_14 = [
    "3.1  Research Design",
    "The project adopts the Design and Development Research methodology (Plomp, 2013): an artefact is constructed and evaluated to solve an identified practical problem.",
    "Stages: (1) requirement gathering; (2) data collection; (3) data preprocessing; (4) machine learning model development; (5) system development; (6) testing; (7) evaluation.",
    "Each stage produced an artefact or report that fed the next: requirements were captured as functional & non-functional specifications; data collection produced the analysis dataset; preprocessing produced a clean modelling table; modelling produced & compared five classifiers; system development produced the web application; testing/evaluation are reported in Chapter Four.",
    "3.2  System Architecture",
    "The system is a three-tier web application:",
    "\u2022  Presentation tier: Bootstrap 5 templates and Chart.js rendered by Flask, plus a JSON API for programmatic access (/api/*).",
    "\u2022  Application tier: Flask blueprints handling authentication, uploads, prediction, reporting and administration.",
    "\u2022  Data tier: SQLAlchemy ORM over SQLite for development and MySQL for production.",
    "The ML service is a separate module that owns preprocessing, training, inference and explanation, so the model can be retrained or replaced without touching the web layer.",
    "Figure 1 shows the three-tier architecture; Figure 2 shows the end-to-end workflow: Student Records \u2192 Data Cleaning \u2192 Feature Extraction \u2192 AI Model (Random Forest) \u2192 Prediction \u2192 Low/Medium/High Risk \u2192 Advisor Alert \u2192 Academic Intervention.",
]
s = add_slide()
section_group_slide(s, 3, "RESEARCH METHODOLOGY", ["3.1  |  3.2"], bullets_14, nxt(), accent=BLUE)

bullets_15 = [
    "3.3  Data Collection",
    "Student records contain 15 attributes (Table 1 in the thesis):",
    "   \u2022  Student ID (text) \u2014 unique matriculation number;   \u2022  Programme (categorical) \u2014 degree programme;   \u2022  Department (categorical) \u2014 owning department;   \u2022  Gender (categorical) \u2014 Male/Female/Other;   \u2022  Age (integer) \u2014 student age in years;   \u2022  Previous GPA (float, 0\u20134) \u2014 cumulative GPA before the semester;   \u2022  Attendance % (float, 0\u2013100);   \u2022  Assignment score (0\u2013100);   \u2022  Quiz score (0\u2013100);   \u2022  Mid-semester score (0\u2013100);   \u2022  Continuous assessment (0\u2013100);   \u2022  Study hours (float);   \u2022  Examination score / Final score / Final GPA \u2014 outcomes, ground truth only.",
    "Data may be obtained from the university\u2019s academic records with appropriate authorization or from publicly available educational datasets.",
    "Because institutional records were not available during development, the project used a reproducible synthetic cohort of 2,550 student records whose statistical relationships mirror published findings, with deliberately injected missing values (\u22483% per numeric field) and duplicate rows (\u22482%) so the cleaning pipeline is exercised end-to-end.",
    "3.4  Data Preprocessing",
    "The preprocessing stage performs, in order:",
    "   1. Column normalisation & aliasing \u2014 headers lower-cased and mapped to canonical schema (e.g. Attendance \u2192 attendance_pct, Matric No \u2192 student_id, CA \u2192 continuous_assessment).",
    "   2. Removing duplicate records \u2014 exact duplicate rows dropped.",
    "   3. Type coercion & range validation \u2014 numeric fields parsed numerically; out-of-range values (attendance >100, GPA >4, age <15) treated as missing rather than trusted.",
    "   4. Handling missing values \u2014 numeric fields median-imputed, categorical fields mode-imputed (Larose, 2014).",
    "   5. Data normalization \u2014 numeric features standardised (zero mean, unit variance) inside the pipeline so training & inference apply identical transforms.",
    "   6. Encoding categorical variables \u2014 programme, department, gender one-hot encoded with handle_unknown='ignore' so unseen categories at inference don\u2019t break prediction.",
    "   7. Feature selection \u2014 11 pre-examination features retained; outcome columns excluded from inputs to prevent target leakage.",
    "Steps 5\u20137 are one scikit-learn ColumnTransformer inside the model pipeline, guaranteeing the exact transformations used in training are replayed at inference.",
    "3.5  Feature Selection and Target Definition",
    "The modelling contract separates predictors (available mid-semester) from outcomes (available only after the examination).",
    "Predictors (11): age, previous_gpa, attendance_pct, assignment_score, quiz_score, mid_sem_score, continuous_assessment, study_hours, programme, department, gender.",
    "Target: a three-level academic risk band derived from the final score (Table 2):",
    "   \u2022  Low Risk \u2014 final score \u226570 (on track / likely to excel);   \u2022  Medium Risk \u2014 final score 50\u201369.99 (moderate; watch-list);   \u2022  High Risk \u2014 final score <50 (at risk of failing; immediate intervention).",
    "Examination score, final score and final GPA are used only as ground truth for training and evaluation.",
    "Prediction is generated BEFORE the final examination, so the target is derived from outcomes while inputs are strictly pre-examination \u2014 the operational equivalent of forecasting the outcome from the mid-semester snapshot.",
]
s = add_slide()
section_group_slide(s, 3, "RESEARCH METHODOLOGY", ["3.3  |  3.4  |  3.5"], bullets_15, nxt(),
                    accent=BLUE)

bullets_16 = [
    "3.6  Machine Learning Model",
    "The Random Forest Classifier is used as the primary model. Reasons:",
    "   \u2022  High prediction accuracy on tabular educational data;",
    "   \u2022  Handles large datasets and many features efficiently;",
    "   \u2022  Resistant to overfitting via bagging and random feature subsets (Breiman, 2001);",
    "   \u2022  Class-weight balancing accommodates the smaller High-Risk band;",
    "   \u2022  Native feature-importance analysis supports explainability to lecturers.",
    "Other models \u2014 Decision Tree, Logistic Regression, Na\u00EFve Bayes (Gaussian) and Support Vector Machine (RBF kernel, probability-calibrated) \u2014 are tested for comparison, following the baseline practice of James et al. (2013).",
    "Experimental protocol: cleaned dataset split 80:20 (stratified, random seed 42) into 2,000 train / 500 hold-out.",
    "Each candidate additionally evaluated with 5-fold stratified cross-validation on the training set (mean F1 \u00B1 SD).",
    "The model with the highest cross-validated F1 is selected (more robust to sampling noise than a single test-split score), refitted on training data, evaluated once on hold-out, and persisted with its preprocessing pipeline, cohort statistics and feature importances as model.joblib, alongside metrics.json and evaluation plots.",
    "3.7  System Development Tools",
    "The system was built with (Table 3 in the thesis):",
    "   \u2022  Python 3 \u2014 dominant language for ML and web back ends;   \u2022  Flask 3 \u2014 lightweight, extensible, blueprint-based;   \u2022  Flask-Login \u2014 session management & RBAC;   \u2022  Flask-WTF \u2014 server-side validation & CSRF;   \u2022  Bootstrap 5 + Chart.js \u2014 responsive UI & dashboard charts;   \u2022  MySQL (SQLite dev) \u2014 as specified for the institution;   \u2022  SQLAlchemy (Flask-SQLAlchemy) \u2014 database-agnostic ORM;   \u2022  scikit-learn, pandas, NumPy \u2014 modelling, preprocessing, evaluation;   \u2022  Matplotlib \u2014 reproducible evaluation figures;   \u2022  joblib \u2014 efficient persistence of fitted pipelines;   \u2022  Waitress / Gunicorn (WSGI) \u2014 thread-safe deployment;   \u2022  pytest \u2014 automated unit, integration & system tests.",
    "3.8  System Workflow",
    "Operational workflow implemented by the system:",
    "   1. Lecturer uploads student records (CSV) or enters a single student\u2019s snapshot.",
    "   2. System preprocesses data (deduplicate, validate, impute, encode).",
    "   3. AI model analyses data and outputs calibrated class probabilities.",
    "   4. Performance prediction generated for every student.",
    "   5. Students categorised as Low Risk, Medium Risk or High Risk.",
    "   6. Dashboard displays predictions, distributions and early-warning alerts.",
    "   7. Academic advisors receive recommendations for intervention and record the action taken, closing the loop with tracked follow-up.",
    "Figure 2 shows the end-to-end flow: Student Records \u2192 Data Cleaning \u2192 Feature Extraction \u2192 AI Model (Random Forest) \u2192 Prediction \u2192 Low Risk / Medium & High Risk \u2192 Advisor Alert \u2192 Academic Intervention.",
]
s = add_slide()
section_group_slide(s, 3, "RESEARCH METHODOLOGY", ["3.6  |  3.7  |  3.8"], bullets_16, nxt(), accent=BLUE)

bullets_17 = [
    "3.9  Functional Requirements",
    "The system shall (Table 4 in the thesis):",
    "   FR1  Allow secure login with username/password and role-based access (admin, lecturer, advisor);   FR2  Upload student data as validated CSV files (with downloadable template);   FR3  Predict academic performance for a single student via a web form;   FR4  Batch-predict every student in an uploaded dataset and store results;   FR5  Identify at-risk students and rank them by risk level and confidence;   FR6  Generate intervention recommendations from the factors driving each prediction;   FR7  Generate reports: risk distributions, departmental tables, CSV export, printable pages;   FR8  Display charts & statistics (risk distribution, department comparison, model metrics);   FR9  Record & track advisor interventions (action, notes, status) per student;   FR10  Manage user accounts (create users, assign roles) \u2014 administrator only;   FR11  Retrain the model and re-score all students \u2014 administrator only;   FR12  Expose a REST JSON API for all core operations.",
    "3.10  Non-Functional Requirements",
    "The system shall meet (Table 5 in the thesis):",
    "   NFR1  Fast response time \u2014 prediction <1 s; dashboard pages <2 s;   NFR2  High accuracy \u2014 \u226570% held-out accuracy (acceptance gate enforced at training time);   NFR3  Secure authentication \u2014 hashed passwords, CSRF protection, session hardening, role checks;   NFR4  Easy-to-use interface \u2014 consistent Bootstrap UI, guided forms, downloadable CSV template;   NFR5  Reliable performance \u2014 idempotent setup, cached model loading, health endpoint for monitoring;   NFR6  Portability \u2014 runs on Windows/Linux, SQLite or MySQL via configuration only;   NFR7  Maintainability \u2014 51 automated tests, modular blueprints/services, pinned dependencies;   NFR8  Data protection \u2014 access-controlled records; no credentials or personal data in logs.",
    "3.11  Testing Strategy",
    "Four levels of testing are applied (Pressman & Maxim, 2020; Table 6 in the thesis):",
    "   \u2022  Unit testing \u2014 individual functions/modules: column aliasing, duplicate removal, imputation, risk banding, recommendation rules;",
    "   \u2022  Integration testing \u2014 module interactions: upload \u2192 clean \u2192 persist \u2192 predict; API \u2192 service \u2192 model;",
    "   \u2022  System testing \u2014 end-to-end application behaviour: login flows, permissions, all pages, exports, plots, error pages;",
    "   \u2022  User acceptance testing \u2014 workflows against acceptance criteria: lecturer uploads & sees alerts; advisor records interventions; admin re-trains.",
    "All automated tests executed with pytest; full results reported in Chapter Four (Table 13).",
    "3.12  Evaluation Metrics",
    "Model performance evaluated using standard classification metrics (James et al., 2013):",
    "   \u2022  Accuracy \u2014 proportion of correctly classified students;   \u2022  Precision \u2014 of students predicted in a band, the proportion truly in that band (weighted & per-class);   \u2022  Recall \u2014 of students truly in a band, the proportion correctly identified (weighted & per-class);   \u2022  F1-Score \u2014 harmonic mean of precision & recall, reported per class, macro-averaged and weighted-averaged;   \u2022  Confusion Matrix \u2014 full actual-vs-predicted count table;   \u2022  Cross-validation F1 \u2014 mean \u00B1 SD over 5 stratified folds, used for model selection.",
    "3.13  Ethical Considerations",
    "Student data is sensitive personal information. The study therefore:",
    "   (a)  used synthetic records during development and requires institutional authorization before real data are loaded;",
    "   (b)  stores only hashed passwords;",
    "   (c)  restricts uploads and intervention records by role;",
    "   (d)  presents predictions as decision support with explicit confidence & factor explanations rather than automated decisions about individuals;",
    "   (e)  documents model limitations so that false negatives are not treated as guarantees of safety.",
]
s = add_slide()
section_group_slide(s, 3, "RESEARCH METHODOLOGY", ["3.9  |  3.10  |  3.11  |  3.12  |  3.13"],
                    bullets_17, nxt(), accent=GOLD,
                    note="Designed as decision support, not a replacement for professional judgement.")

# =====================================================================
# CHAPTER FOUR  (18..21)
# =====================================================================
bullets_18 = [
    "4.1  Experimental Setup",
    "Dataset: the training corpus contained 2,550 raw student records. After cleaning \u2014 removal of 50 duplicate rows and rows lacking an outcome \u2014 2,500 records were used, each described by the 11 pre-examination features listed in Chapter Three (Table 7).",
    "Class distribution: Low Risk 908 records (36.3%); Medium Risk 1,256 records (50.2%); High Risk 336 records (13.4%).",
    "Split: 2,000 train / 500 hold-out (stratified, 80/20, random seed 42).",
    "Validation: 5-fold stratified cross-validation on the training set.",
    "The moderately imbalanced class distribution (the Medium Risk band dominates) reflects typical institutional grade distributions and motivates class-weighted training and per-class reporting.",
    "Environment: Python 3.14, scikit-learn 1.9, pandas 3.0, NumPy 2.5, Matplotlib 3.11 on Windows 11; deterministic random seed 42 for all stochastic components.",
    "Figure 3 shows the distribution of risk levels in the training dataset.",
    "4.2  Model Comparison Results",
    "Five classifiers were trained under identical conditions (Table 8 in the thesis).",
    "Cross-validation scores = mean F1 (weighted) \u00B1 SD over 5 stratified folds; test metrics on the untouched 500-record hold-out.",
    "   \u2022  Random Forest (selected): accuracy 0.830, precision(w) 0.830, recall(w) 0.830, F1(w) 0.829, CV F1 0.833 \u00B1 0.015, train time 5.52 s;",
    "   \u2022  Decision Tree: accuracy 0.752, F1(w) 0.751, CV F1 0.762 \u00B1 0.007;",
    "   \u2022  Logistic Regression: accuracy 0.840, F1(w) 0.840, CV F1 0.826 \u00B1 0.019;",
    "   \u2022  Na\u00EFve Bayes: accuracy 0.838, F1(w) 0.838, CV F1 0.829 \u00B1 0.015;",
    "   \u2022  Support Vector Machine: accuracy 0.848, F1(w) 0.848, CV F1 0.821 \u00B1 0.021.",
    "Every model except the single Decision Tree clears the 70% acceptance threshold \u2014 the feature set carries genuine predictive signal.",
    "SVM records the highest single-split accuracy (84.8%) but the lowest cross-validated F1 (0.821 \u00B1 0.021) \u2014 a favourable split artefact; Random Forest attains the highest cross-validated F1 (0.833 \u00B1 0.015) with the second-smallest variance, so it is selected under the pre-declared selection criterion.",
    "Logistic Regression performs almost as well as Random Forest (84.0% vs 83.0%) \u2014 the problem is largely linearly separable; the Decision Tree\u2019s substantially lower score (75.2%) quantifies the benefit of ensembling.",
    "Figure 4 shows the model comparison on the held-out test set.",
]
s = add_slide()
section_group_slide(s, 4, "EXPERIMENTAL RESULTS AND DISCUSSIONS",
                    ["4.1  |  4.2"], bullets_18, nxt(), accent=BLUE)

bullets_19 = [
    "4.3  Per-Class Performance and Confusion Matrix",
    "Per-class metrics of the selected Random Forest model on the test set (n = 500; Table 9 in the thesis):",
    "   \u2022  Low Risk: precision 0.832, recall 0.868, F1 0.850, support 182;",
    "   \u2022  Medium Risk: precision 0.829, recall 0.833, F1 0.831, support 251;",
    "   \u2022  High Risk: precision 0.828, recall 0.716, F1 0.768, support 67;",
    "   \u2022  Weighted average: precision 0.830, recall 0.830, F1 0.829, support 500;",
    "   \u2022  Macro average: precision 0.830, recall 0.806, F1 0.816.",
    "Confusion matrix (Table 10; rows = actual, columns = predicted):",
    "   \u2022  Actual Low: 158 Low / 24 Medium / 0 High;",
    "   \u2022  Actual Medium: 32 Low / 209 Medium / 10 High;",
    "   \u2022  Actual High: 0 Low / 19 Medium / 48 High.",
    "Precision is remarkably balanced across the three bands (0.828\u20130.832), meaning a student flagged into any band can be trusted at roughly the same rate.",
    "Recall is highest for Low Risk (0.868) and lowest for High Risk (0.716): 19 of 67 truly at-risk students were predicted Medium Risk.",
    "Importantly, NO High-Risk student was predicted Low Risk (the bottom-left cell is zero), so the most dangerous error type \u2014 silently clearing a failing student \u2014 did not occur in this evaluation.",
    "Medium-band confusions dominate because students near the 50/70 score boundaries are inherently ambiguous.",
    "Figure 5 shows the confusion matrix of the selected Random Forest model.",
    "4.4  Feature Importance and Interpretation",
    "The Random Forest reports impurity-based feature importances for the deployed pipeline (Table 11 in the thesis):",
    "   1.  Continuous assessment \u2014 0.2290;   2.  Previous GPA \u2014 0.1644;   3.  Mid-semester score \u2014 0.1324;   4.  Assignment score \u2014 0.1274;   5.  Quiz score \u2014 0.1089;   6.  Attendance percentage \u2014 0.0828;   7.  Study hours \u2014 0.0816;   8.  Age \u2014 0.0253;   9\u201325  Programme / department / gender levels \u2014 \u22480.048 combined.",
    "Figure 6 shows the top 15 feature importances of the selected model.",
    "The ranking confirms the EDM literature: continuous assessment, previous GPA and mid-semester score are the strongest predictors, while demographic features contribute comparatively little.",
]
s = add_slide()
section_group_slide(s, 4, "EXPERIMENTAL RESULTS AND DISCUSSIONS",
                    ["4.3  |  4.4"], bullets_19, nxt(), accent=BLUE)

bullets_20 = [
    "4.5  Discussion Relative to the Research Questions",
    "RQ1 \u2014 Which academic factors significantly influence student performance?",
    "   Continuous assessment, previous GPA and mid-semester score are the strongest predictors; assessment engagement & prior attainment dominate; demographic variables contribute comparatively little (Table 12 in the thesis).",
    "RQ2 \u2014 Which machine learning algorithm provides the highest prediction accuracy?",
    "   Random Forest on cross-validated F1 (0.833 \u00B1 0.015) \u2014 robust across folds; SVM\u2019s higher single-split accuracy is a favourable split artefact.",
    "RQ3 \u2014 How can AI assist lecturers in identifying at-risk students early?",
    "   Calibrated risk bands from a mid-semester snapshot, surfaced on role-based dashboards with ranked alerts and factor explanations.",
    "RQ4 \u2014 Can early prediction improve academic intervention strategies?",
    "   Yes \u2014 decision support surfaces at-risk students before finals, with rule-based recommendations and a tracked intervention record per student.",
    "Table 12 (in the thesis) summarises the answers to the research questions.",
    "4.6  System Implementation",
    "The deployed system is a role-based Flask web application with the following pages and capabilities:",
    "   \u2022  Login interface (Figure 7) with role-based access control;",
    "   \u2022  Early-warning dashboard (Figure 8) showing risk distributions, alerts and key statistics;",
    "   \u2022  Student records with risk filters (Figure 9);",
    "   \u2022  Student detail with prediction, factors and interventions (Figure 10);",
    "   \u2022  Model performance page (Figure 11);",
    "   \u2022  Reports page with advisor work-list (Figure 12).",
    "Frontend is Bootstrap 5 + Chart.js; backend is Flask with auth, main and API blueprints; the ML service is a separate module (preprocess \u2192 train \u2192 evaluate \u2192 predict \u2192 recommend).",
    "The system is production-grade (tests passing, security headers, RBAC, health endpoint) and served via Docker + MySQL / Waitress.",
]
s = add_slide()
section_group_slide(s, 4, "EXPERIMENTAL RESULTS AND DISCUSSIONS",
                    ["4.5  |  4.6"], bullets_20, nxt(), accent=BLUE,
                    note="Decision support surfaces at-risk students before finals, not after failure.")

bullets_21 = [
    "4.7  System Testing and User Acceptance",
    "Automated system test results (Table 13 in the thesis): 51 automated tests passed, covering unit, integration, system and user-acceptance scenarios.",
    "User-acceptance test results (Table 14): lecturer uploads and sees alerts; advisor records interventions; admin re-trains and re-scores.",
    "Testing confirms the system meets the functional requirements FR1\u2013FR12 and the non-functional requirements NFR1\u2013NFR8.",
    "4.8  Performance Evaluation",
    "Single-student prediction: mean 184 ms.",
    "Batch prediction of 1,000 students: 275 ms.",
    "Dashboard pages render under 2 s; prediction endpoint under 1 s (NFR1 met).",
    "Held-out accuracy 0.830 \u2265 70% acceptance gate (NFR2 met).",
    "Deterministic seed 42 throughout \u2014 reproducible results.",
    "Performance benchmarks summarised in Table 15 (in the thesis).",
    "4.9  General Discussion",
    "The experiment confirms that a mid-semester snapshot of academic indicators carries enough signal to predict three-level academic risk with useful accuracy.",
    "The selected Random Forest model is both accurate and explainable: feature importances make it possible to tell lecturers not only who is at risk but also why.",
    "The most important practical result is that no High-Risk student was predicted Low Risk in this evaluation \u2014 the most dangerous error type was avoided.",
    "The system is designed as decision support, not a replacement for professional judgement; every prediction must be reviewed by a lecturer or advisor alongside contextual knowledge.",
    "The main limitation is that results are based on synthetic data; real-data accuracy remains to be measured under institutional authorization.",
]
s = add_slide()
section_group_slide(s, 4, "EXPERIMENTAL RESULTS AND DISCUSSIONS",
                    ["4.7  |  4.8  |  4.9"], bullets_21, nxt(), accent=BLUE)

# =====================================================================
# CHAPTER FIVE  (22..23)
# =====================================================================
bullets_22 = [
    "5.1  Summary",
    "An AI-based academic performance prediction system was designed and developed end-to-end.",
    "It analyses mid-semester student data and classifies each student into Low / Medium / High risk.",
    "A Design and Development methodology was followed; the artefact was built and evaluated.",
    "Five classifiers were compared under an 80/20 stratified split and 5-fold cross-validation.",
    "Random Forest was selected on the strength of the best cross-validated F1 (0.833 \u00B1 0.015).",
    "Held-out accuracy 0.830; weighted F1 0.829; per-class F1 0.850 / 0.831 / 0.768.",
    "Continuous assessment, previous GPA and mid-semester score are the strongest predictors.",
    "The model is deployed in a role-based Flask web app with dashboards, alerts, recommendations and an intervention tracker \u2014 51 tests passing; served via Docker + MySQL / Waitress.",
    "5.2  Findings",
    "AI-driven early-warning prediction is feasible, accurate and actionable within a university setting.",
    "The system converts routine mid-semester records into prioritised risk alerts and concrete intervention recommendations, enabling support before final examinations rather than after failure.",
    "Random Forest was the best model under the pre-declared selection criterion (highest cross-validated F1).",
    "Per-class precision is balanced (0.828\u20130.832), so a flag in any band is equally trustworthy.",
    "No High-Risk student was predicted Low Risk \u2014 the most dangerous error type was avoided in this evaluation.",
    "Continuous assessment, previous GPA and mid-semester score are the strongest predictors; demographic features contribute comparatively little.",
    "The model is deployed in a role-based web app with 51 automated tests and served via Docker + MySQL / Waitress.",
    "5.3  Conclusion",
    "The aim of this project was to develop an AI-based system that predicts university students\u2019 academic performance and assists lecturers and academic advisors in identifying academically at-risk students at an early stage.",
    "This aim was achieved: the system was designed, built, evaluated and deployed.",
    "The system is production-grade (tests passing, security headers, RBAC, health endpoint) and served via Docker + MySQL / Waitress.",
    "Its accuracy depends on data quality, so it is designed as decision support for lecturers and advisors rather than a replacement for professional judgement.",
    "Every prediction must be reviewed by a lecturer or advisor alongside professional judgement.",
]
s = add_slide()
section_group_slide(s, 5, "CONCLUDING REMARKS",
                    ["5.1  |  5.2  |  5.3"], bullets_22, nxt(), accent=BLUE)

bullets_23 = [
    "5.4  Recommendations",
    "Deploy the system with institutional authorization and real student data.",
    "Train lecturers and advisors to interpret risk bands alongside professional judgement.",
    "Integrate with the existing Student Information System for seamless data flow.",
    "Track interventions longitudinally to close the feedback loop and improve the model over time.",
    "Monitor model drift and retrain periodically as new data accrue.",
    "Present predictions as decision support with explicit confidence and factor explanations, never as automated decisions about individuals.",
    "5.5  Limitations",
    "The study used synthetic training data; real-data accuracy has not yet been measured.",
    "The scope is limited to a single institution and a single cohort.",
    "No longitudinal tracking across several cohorts was performed; no formal user study with large samples was conducted.",
    "Institutional deployment concerns such as integration with an existing Student Information System, longitudinal tracking and formal user studies are outside the current scope.",
    "5.6  Future Work",
    "Replace synthetic data with authorized institutional records; add longitudinal tracking and cohort comparison.",
    "Introduce model drift monitoring and periodic retraining; explore deep models and LMS clickstream features.",
    "Run a controlled user study with large samples to measure real-world impact.",
    "Extend the system to cover dropout prediction and GPA prediction in addition to risk-banding.",
]
s = add_slide()
section_group_slide(s, 5, "CONCLUDING REMARKS",
                    ["5.4  |  5.5  |  5.6"], bullets_23, nxt(), accent=GOLD)

# =====================================================================
# REFERENCES  (24)
# =====================================================================
refs = [
    "Baker, R.S. & Inventado, P.S. (2014). Educational Data Mining and Learning Analytics. In Spector, J.M. et al. (eds.), Learning Analytics. Springer.",
    "Bishop, C.M. (2006). Pattern Recognition and Machine Learning. Springer.",
    "Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5\u201332.",
    "Holmes, W. et al. (2019). Artificial Intelligence in Education. Center for Curriculum Redesign.",
    "James, G. et al. (2013). An Introduction to Statistical Learning. Springer.",
    "Kotsiantis, S. et al. (2004). Predicting Student Profile in Distance Learning Using Naive Bayes. Educational Technology & Society.",
    "Larose, D.T. (2014). Data Mining and Predictive Analytics. Wiley.",
    "Luckin, R. et al. (2016). Intelligence Unleashed: An argument for AI in Education. Pearson.",
    "Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. JMLR, 12, 2825\u20132830.",
    "Pena-Ayala, A. (2014). Learning Analytics: Educational Measurements Using Data Analytics. Springer.",
    "Plomp, T. (2013). Educational Design Research. SLO / UNDP.",
    "Pressman, R.S. & Maxim, B.R. (2020). Software Engineering: A Practitioner\u2019s Approach. McGraw-Hill.",
    "Romero, C. & Ventura, S. (2010). Educational Data Mining: A Review of the State of the Art. IEEE Trans. SMC, 40(6), 131\u2013151.",
    "Siemens, G. & Long, P. (2011). Penetrating the Fog: Analytics in Learning and Education. EDUCAUSE Review, 46(5).",
    "Vapnik, V. (1998). Statistical Learning Theory. Wiley.",
    "Zawacki-Richter, O. et al. (2019). Systematic Review of Research on AI Applications in Higher Education. IJETHE.",
]
s = add_slide()
set_bg(s, NAVY)
top_bar(s, BLUE, 0.10)
txt(s, Inches(0.6), Inches(0.42), Inches(12), Inches(0.55), "REFERENCES", 26, WHITE, bold=True)
line_h(s, Inches(0.6), Inches(0.98), Inches(12.1), RGBColor(0x2A,0x35,0x52), 1.0)
# two-column refs
import math
n = len(refs)
half = math.ceil(n/2)
cw = (W - Inches(1.2) - Inches(0.3))/2
for c in range(2):
    x = Inches(0.6) + c*(cw+Inches(0.3))
    yy = Inches(1.18)
    sub = refs[c*half:(c+1)*half] if c==0 else refs[half:]
    for r in sub:
        paras(s, x, yy, cw-Inches(0.1), Inches(0.4), [r], sz=11.5, c=LIGHT, ls=1.18, gap_after=5)
        approx = max(1, int(len(r)/(48)) + (1 if ";" in r else 0))
        yy = yy + Inches(0.20)*approx + Inches(0.05)
brand_footer(s, nxt())

# =====================================================================
# THANK YOU  (25)
# =====================================================================
s = add_slide()
set_bg(s, NAVY)
top_bar(s, GOLD, 0.14)
rect(s, Inches(0), Inches(0.14), Inches(0.10), H-Inches(0.14), BLUE_D)
rect(s, W/2-Inches(2.0), Inches(2.7), Inches(4.0), Inches(0.06), BLUE)
txt(s, Inches(0.5), Inches(3.0), W-Inches(1.0), Inches(1.2),
    "THANK YOU", 52, WHITE, bold=True, al=PP_ALIGN.CENTER)
txt(s, Inches(0.5), Inches(4.1), W-Inches(1.0), Inches(0.8),
    "Questions & Discussion", 22, LIGHT, al=PP_ALIGN.CENTER)
rect(s, Inches(4.6), Inches(5.15), Inches(4.13), Inches(0.04), GOLD)
txt(s, Inches(0.5), Inches(5.3), W-Inches(1.0), Inches(0.4),
    STUDENT, 18, WHITE, bold=True, al=PP_ALIGN.CENTER)
txt(s, Inches(0.5), Inches(5.72), W-Inches(1.0), Inches(0.34), IDLINE, 13, MUTE, al=PP_ALIGN.CENTER)
txt(s, Inches(0.5), Inches(6.05), W-Inches(1.0), Inches(0.34), DEPT, 13, MUTE, al=PP_ALIGN.CENTER)
txt(s, Inches(0.5), Inches(6.38), W-Inches(1.0), Inches(0.34), "UNIVERSITY OF GHANA", 13, MUTE, al=PP_ALIGN.CENTER)
txt(s, Inches(0.5), Inches(6.78), W-Inches(1.0), Inches(0.34), DATE, 12, GREY, ital=True, al=PP_ALIGN.CENTER)
brand_footer(s, nxt())

# =====================================================================
# SAVE
# =====================================================================
out = "UG SLIDE TEMPLATE.pptx"
prs.save(out)
print("SAVED:", out)
print("SLIDES:", len(prs.slides._sldIdLst))
print("PAGE COUNT USED:", page)
