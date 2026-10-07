"""Smoke tests for the server-rendered interface (all pages reachable)."""
from __future__ import annotations

import io


def test_index_redirects_anonymous_to_login(client):
    res = client.get("/")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_dashboard_renders_for_lecturer(lecturer_client):
    res = lecturer_client.get("/dashboard")
    assert res.status_code == 200
    assert b"Early-warning dashboard" in res.data
    assert b"High risk" in res.data


def test_login_page_renders(client):
    res = client.get("/login")
    assert res.status_code == 200
    assert b"EduRisk Predictor" in res.data


def test_students_page_and_filters(lecturer_client):
    res = lecturer_client.get("/students")
    assert res.status_code == 200
    assert b"Predicted risk" in res.data

    res = lecturer_client.get("/students?risk=High%20Risk&page=1")
    assert res.status_code == 200

    res = lecturer_client.get("/students?q=STU00001")
    assert res.status_code == 200


def test_student_detail_page(lecturer_client):
    body = lecturer_client.get("/api/students?per_page=1").get_json()
    student_id = body["items"][0]["id"]
    res = lecturer_client.get(f"/students/{student_id}")
    assert res.status_code == 200
    assert b"Predicted risk" in res.data
    assert b"Student record" in res.data


def test_predict_page_get_and_post(lecturer_client):
    res = lecturer_client.get("/predict")
    assert res.status_code == 200
    assert b"Predict a student" in res.data

    res = lecturer_client.post(
        "/predict",
        data={
            "full_name": "Form Student",
            "programme": "BSc Economics",
            "department": "Economics",
            "gender": "Female",
            "age": "20",
            "previous_gpa": "1.3",
            "attendance_pct": "35",
            "assignment_score": "30",
            "quiz_score": "28",
            "mid_sem_score": "31",
            "continuous_assessment": "29",
            "study_hours": "3",
        },
    )
    assert res.status_code == 200
    assert b"Prediction result" in res.data
    assert b"Recommended interventions" in res.data


def test_predict_page_validates_numeric_ranges(lecturer_client):
    res = lecturer_client.post(
        "/predict",
        data={
            "full_name": "Bad Student",
            "previous_gpa": "9.5",
            "attendance_pct": "150",
            "assignment_score": "50",
            "quiz_score": "50",
            "mid_sem_score": "50",
            "continuous_assessment": "50",
        },
    )
    assert res.status_code == 200
    assert b"Number must be between" in res.data


def test_upload_page_roles(lecturer_client, advisor_client):
    assert lecturer_client.get("/upload").status_code == 200
    res = advisor_client.get("/upload")
    assert res.status_code == 302  # advisors may not upload
    assert "/dashboard" in res.headers["Location"]


def test_template_download(lecturer_client):
    res = lecturer_client.get("/upload/template.csv")
    assert res.status_code == 200
    assert b"student_id" in res.data


def test_reports_page(lecturer_client):
    res = lecturer_client.get("/reports")
    assert res.status_code == 200
    assert b"Top high-risk students" in res.data


def test_reports_csv_export(lecturer_client):
    res = lecturer_client.get("/reports/export.csv")
    assert res.status_code == 200
    assert "text/csv" in res.content_type


def test_model_page(admin_client):
    res = admin_client.get("/model")
    assert res.status_code == 200
    assert b"Model comparison" in res.data
    assert b"Random Forest" in res.data


def test_model_page_role_access(admin_client, lecturer_client, advisor_client):
    # Model transparency is for admin + lecturers (who run predictions);
    # advisors are sent back to their work-list.
    assert admin_client.get("/model").status_code == 200
    assert lecturer_client.get("/model").status_code == 200
    res = advisor_client.get("/model")
    assert res.status_code == 302
    assert "/dashboard" in res.headers["Location"]
    # advisors also have no access to user management
    res = advisor_client.get("/users")
    assert res.status_code == 302


def test_users_page_admin(admin_client):
    res = admin_client.get("/users")
    assert res.status_code == 200
    assert b"Create a user" in res.data

    res = admin_client.post(
        "/users",
        data={
            "username": "newlecturer",
            "full_name": "New Lecturer",
            "email": "newlecturer@university.edu",
            "role": "lecturer",
            "password": "StrongPass123",
        },
    )
    assert res.status_code == 302
    follow = admin_client.get("/users")
    assert b"newlecturer" in follow.data


def test_plot_served(admin_client):
    res = admin_client.get("/plots/confusion_matrix.png")
    assert res.status_code == 200
    assert res.content_type.startswith("image/")


def test_404_page(lecturer_client):
    res = lecturer_client.get("/no-such-page")
    assert res.status_code == 404
    assert b"404" in res.data


def test_intervention_form_via_web(advisor_client, lecturer_client):
    body = lecturer_client.get("/api/students?per_page=1").get_json()
    student_id = body["items"][0]["id"]
    res = advisor_client.post(
        f"/students/{student_id}/interventions",
        data={
            "action": "Mentoring / tutoring",
            "notes": "Paired with a peer tutor",
            "status": "in_progress",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Intervention recorded" in res.data


# --------------------------------------------------------------------------- #
# Role-based workspaces
# --------------------------------------------------------------------------- #
def test_interventions_page_roles(advisor_client, admin_client, lecturer_client):
    """Interventions workspace: advisor + admin only."""
    res = advisor_client.get("/interventions")
    assert res.status_code == 200
    assert b"Intervention log" in res.data
    assert b"Interventions" in res.data

    assert admin_client.get("/interventions").status_code == 200

    res = lecturer_client.get("/interventions")
    assert res.status_code == 302
    assert "/dashboard" in res.headers["Location"]


def test_dashboard_role_content(admin_client, lecturer_client, advisor_client):
    """Each role gets a workspace tailored to its job."""
    # --- lecturer: cohort monitoring + upload focus ---
    res = lecturer_client.get("/dashboard")
    body = res.data.decode()
    assert res.status_code == 200
    assert "Early-warning dashboard" in body
    assert "Data freshness" in body
    assert "Upload fresh records" in body
    assert "Priority queue" not in body

    # --- advisor: at-risk queue + intervention coverage ---
    res = advisor_client.get("/dashboard")
    body = res.data.decode()
    assert res.status_code == 200
    assert "At-risk work-list" in body
    assert "Priority queue" in body
    assert "Needs intervention" in body
    assert "Data freshness" not in body
    assert "Early-warning alerts" not in body

    # --- admin: institutional overview + system status ---
    res = admin_client.get("/dashboard")
    body = res.data.decode()
    assert res.status_code == 200
    assert "Institutional overview" in body
    assert "System status" in body
    assert "Registered users" in body
    assert "Priority queue" not in body


def test_sidebar_navigation_per_role(admin_client, lecturer_client, advisor_client):
    """The sidebar only advertises links the role may actually open."""
    admin_nav = admin_client.get("/dashboard").data.decode()
    for path in ("/upload", "/interventions", "/model", "/users"):
        assert f'href="{path}"' in admin_nav, f"admin sidebar missing {path}"

    lecturer_nav = lecturer_client.get("/dashboard").data.decode()
    assert 'href="/upload"' in lecturer_nav
    assert 'href="/model"' in lecturer_nav
    assert 'href="/users"' not in lecturer_nav
    assert 'href="/interventions"' not in lecturer_nav

    advisor_nav = advisor_client.get("/dashboard").data.decode()
    assert 'href="/interventions"' in advisor_nav
    assert 'href="/upload"' not in advisor_nav
    assert 'href="/model"' not in advisor_nav
    assert 'href="/users"' not in advisor_nav


def test_lecturer_cannot_open_interventions_page(lecturer_client):
    # Deep links are blocked server-side, not just hidden in the sidebar.
    res = lecturer_client.get("/interventions")
    assert res.status_code == 302
