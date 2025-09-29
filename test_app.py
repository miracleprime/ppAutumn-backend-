# tests/test_api.py
import pytest
from app import app, db
from models import User, Job, Application

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Создаём тестовых пользователей
            student = User(username="student", password="123", role="student")
            employer = User(username="employer", password="123", role="employer")
            db.session.add_all([student, employer])
            db.session.commit()
        yield client

# 1. Регистрация нового пользователя
def test_register_user(client):
    resp = client.post("/register", json={"username": "testuser", "password": "pass", "role": "student"})
    assert resp.status_code == 201

# 2. Логин существующего пользователя
def test_login_user(client):
    resp = client.post("/login", json={"username": "student", "password": "123"})
    assert resp.status_code in [200, 302]  # может быть редирект

# 3. Создание вакансии работодателем
def test_create_job(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 2  # employer
        sess["role"] = "employer"
    resp = client.post("/api/jobs", json={"title": "Test Job", "description": "Test desc", "type": "internship"})
    assert resp.status_code == 201

# 4. Получение списка вакансий
def test_get_jobs(client):
    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    assert isinstance(resp.json, list)

# 5. Подача отклика студентом
def test_apply_job(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # student
        sess["role"] = "student"
    resp = client.post("/api/applications", json={"job_id": 1})
    assert resp.status_code == 201

# 6. Получение списка откликов
def test_get_applications(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "student"
    resp = client.get("/api/applications")
    assert resp.status_code == 200

# 7. Обновление профиля
def test_update_profile(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "student"
    resp = client.put("/api/profile", json={"full_name": "Иван Иванов", "course": "3", "faculty": "ФКН"})
    assert resp.status_code == 200
    assert "успешно" in resp.json.get("message", "").lower()
