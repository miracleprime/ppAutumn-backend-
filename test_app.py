# test_app.py
import pytest
from app import app, db
from models import Job

@pytest.fixture(autouse=True)
def setup_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

def test_register_user():
    client = app.test_client()
    resp = client.post("/register", data={"username": "student1", "password": "123", "role": "student"})
    assert resp.status_code in (200, 302)

def test_login_user():
    client = app.test_client()
    client.post("/register", data={"username": "student2", "password": "123", "role": "student"})
    resp = client.post("/login", data={"username": "student2", "password": "123"})
    assert resp.status_code in (200, 302)

def test_create_job():
    client = app.test_client()
    client.post("/register", data={"username": "employer1", "password": "123", "role": "employer"})
    client.post("/login", data={"username": "employer1", "password": "123"})
    resp = client.post("/api/jobs", json={"title": "Test job", "description": "Some desc", "job_type": "internship"})
    assert resp.status_code == 201

def test_get_jobs():
    client = app.test_client()
    client.post("/register", data={"username": "employer2", "password": "123", "role": "employer"})
    client.post("/login", data={"username": "employer2", "password": "123"})
    client.post("/api/jobs", json={"title": "Test job2", "description": "Some desc", "job_type": "internship"})
    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

def test_apply_job():
    client = app.test_client()
    client.post("/register", data={"username": "employer3", "password": "123", "role": "employer"})
    client.post("/login", data={"username": "employer3", "password": "123"})
    client.post("/api/jobs", json={"title": "Test job3", "description": "Some desc", "job_type": "internship"})
    with app.app_context():
        job_id = Job.query.first().id

    client.get("/logout")
    client.post("/register", data={"username": "student3", "password": "123", "role": "student"})
    client.post("/login", data={"username": "student3", "password": "123"})
    resp = client.post(f"/api/jobs/{job_id}/apply", json={"resume_url": "link", "cover_letter": "Hi"})
    assert resp.status_code == 201

def test_get_applications():
    client = app.test_client()
    client.post("/register", data={"username": "employer4", "password": "123", "role": "employer"})
    client.post("/login", data={"username": "employer4", "password": "123"})
    client.post("/api/jobs", json={"title": "Test job4", "description": "Some desc", "job_type": "internship"})
    with app.app_context():
        job_id = Job.query.first().id

    client.get("/logout")
    client.post("/register", data={"username": "student4", "password": "123", "role": "student"})
    client.post("/login", data={"username": "student4", "password": "123"})
    client.post(f"/api/jobs/{job_id}/apply", json={"resume_url": "link", "cover_letter": "Hi"})

    resp = client.get("/api/applications")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)

def test_update_profile():
    client = app.test_client()
    client.post("/register", data={"username": "student5", "password": "123", "role": "student"})
    client.post("/login", data={"username": "student5", "password": "123"})
    resp = client.put("/api/profile", json={"full_name": "Иванов Иван", "course": "2", "faculty": "ФКН"})
    assert resp.status_code == 200
