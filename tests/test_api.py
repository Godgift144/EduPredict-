"""End-to-end API tests: auth, prediction, upload, roles."""
from __future__ import annotations

import io
import json


def test_health_endpoint_reports_model_state(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ok"
    assert body["model_ready"] is True
    assert body["database"] is True


def test_api_requires_authentication(client):
    res = client.get("/api/students")
    assert res.status_code == 401
    assert res.is_json


def test_login_success_and_logout(app):
    client = app.test_client()
    res = client.post("/login", data={"username": "lecturer", "password": "Lecturer@1234"})
    assert res.status_code == 302
    res = client.get("/api/summary")
    assert res.status_code == 200
    client.post("/logout")
    assert client.get("/api/summary").status_code == 401


def test_login_rejects_bad_password(app):
    client = app.test_client()
    res = client.post("/login", data={"username": "lecturer", "password": "wrong"})
    assert res.status_code == 401
    assert b"Invalid username or password" in res.data


def test_summary_shape(lecturer_client):
    body = lecturer_client.get("/api/summary").get_json()
    for key in ("total_students", "scored_students", "risk_counts", "high_risk", "at_risk_pct"):
        assert key in body
    assert set(body["risk_counts"]) == {"Low Risk", "Medium Risk", "High Risk"}


def test_predict_endpoint_high_risk(lecturer_client):
    payload = {
        "student_id": "API1",
        "full_name": "API Student",
        "programme": "BSc Computer Science",
        "department": "Computer Science",
        "gender": "Male",
        "age": 19,
        "previous_gpa": 1.1,
        "attendance_pct": 30,
        "assignment_score": 25,
        "quiz_score": 28,
        "mid_sem_score": 24,
        "continuous_assessment": 26,
        "study_hours": 1,
    }
    res = lecturer_client.post("/api/predict", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    body = res.get_json()
    assert body["risk_label"] in ("High Risk", "Medium Risk")
    assert body["recommendations"]
    assert abs(body["prob_low"] + body["prob_medium"] + body["prob_high"] - 1.0) < 1e-3


def test_predict_endpoint_rejects_empty_body(lecturer_client):
    res = lecturer_client.post("/api/predict", data=json.dumps({}), content_type="application/json")
    assert res.status_code == 400


def test_upload_and_students_flow(lecturer_client, sample_csv_bytes):
    res = lecturer_client.post(
        "/upload",
        data={"file": (sample_csv_bytes, "students.csv")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 200  # HTML page re-rendered with success flash
    assert b"2 row(s) imported" in res.data

    body = lecturer_client.get("/api/students?q=TEST90001").get_json()
    assert body["total"] >= 1
    item = body["items"][0]
    assert item["prediction"] is not None
    assert item["prediction"]["risk"] in ("High Risk", "Medium Risk", "Low Risk")

    detail = lecturer_client.get(f"/api/students/{item['id']}").get_json()
    assert detail["student_id"] == "TEST90001"
    assert "interventions" in detail


def test_upload_rejects_bad_filetype(lecturer_client):
    res = lecturer_client.post(
        "/upload",
        data={"file": (io.BytesIO(b"binary"), "notes.pdf")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    assert b"Only .csv files are allowed" in res.data or b"Invalid upload" in res.data


def test_upload_requires_required_columns(lecturer_client):
    bad = io.BytesIO(b"student_id,name\n1,John\n")
    res = lecturer_client.post(
        "/upload",
        data={"file": (bad, "bad.csv")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    assert b"Missing required column" in res.data


def test_lecturer_cannot_upload_via_api_forbidden_role(advisor_client, sample_csv_bytes):
    res = advisor_client.post(
        "/api/upload",
        data={"file": (sample_csv_bytes, "students.csv")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 403


def test_advisor_can_record_intervention(advisor_client, lecturer_client):
    body = lecturer_client.get("/api/students?q=TEST90001").get_json()
    student_id = body["items"][0]["id"]
    res = advisor_client.post(
        f"/api/students/{student_id}/interventions",
        data=json.dumps({"action": "Academic counselling", "notes": "Meet next week"}),
        content_type="application/json",
    )
    assert res.status_code == 201
    detail = advisor_client.get(f"/api/students/{student_id}").get_json()
    assert any(i["action"] == "Academic counselling" for i in detail["interventions"])


def test_lecturer_cannot_record_intervention(lecturer_client):
    body = lecturer_client.get("/api/students?q=TEST90001").get_json()
    student_id = body["items"][0]["id"]
    res = lecturer_client.post(
        f"/api/students/{student_id}/interventions",
        data=json.dumps({"action": "Anything"}),
        content_type="application/json",
    )
    assert res.status_code == 403


def test_non_admin_cannot_retrain(lecturer_client):
    res = lecturer_client.post("/api/model/retrain", content_type="application/json")
    assert res.status_code == 403


def test_model_metrics_endpoint(admin_client):
    res = admin_client.get("/api/model/metrics")
    assert res.status_code == 200
    body = res.get_json()
    assert "models" in body and "best_model" in body


def test_csv_export(lecturer_client):
    res = lecturer_client.get("/api/reports/predictions.csv")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    assert b"predicted_risk" in res.data
