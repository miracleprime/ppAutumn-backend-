import pytest
from app import app, db
from models import User, Job, Application
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # тестовая БД
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def register(client, username, password, role="student"):
    return client.post("/register", data={
        "username": username,
        "password": password,
        "role": role
    }, follow_redirects=True)


def login(client, username, password):
    return client.post("/login", data={
        "username": username,
        "password": password
    }, follow_redirects=True)


# ---------------- ТЕСТЫ ----------------

def test_register_success(client):
    """Регистрация нового пользователя проходит успешно"""
    rv = register(client, "student1", "password", "student")
    assert rv.status_code == 200 or rv.status_code == 302


def test_register_duplicate(client):
    """Регистрация с уже существующим логином должна дать ошибку"""
    register(client, "student1", "password", "student")
    rv = register(client, "student1", "password", "student")
    assert b"Пользователь уже существует" in rv.data


def test_login_success(client):
    """Успешный вход"""
    register(client, "student2", "password", "student")
    rv = login(client, "student2", "password")
    assert rv.status_code == 200 or rv.status_code == 302


def test_login_fail(client):
    """Вход с неверным паролем"""
    register(client, "student3", "password", "student")
    rv = login(client, "student3", "wrongpass")
    assert b"Неверный логин или пароль" in rv.data


def test_create_job_as_employer(client):
    """Работодатель может создать вакансию"""
    register(client, "emp1", "password", "employer")
    login(client, "emp1", "password")
    rv = client.post("/api/jobs", json={
        "title": "Test Job",
        "description": "Some description",
        "job_type": "internship"
    })
    assert rv.status_code == 201
    assert b"Вакансия создана" in rv.data


def test_create_job_as_student_forbidden(client):
    """Студент не может создать вакансию"""
    register(client, "stud1", "password", "student")
    login(client, "stud1", "password")
    rv = client.post("/api/jobs", json={
        "title": "Hack Job",
        "description": "Should not work",
        "job_type": "internship"
    })
    assert rv.status_code == 403


def test_apply_for_job(client):
    """Студент может откликнуться на вакансию"""
    # создаём работодателя + вакансию
    register(client, "emp2", "password", "employer")
    login(client, "emp2", "password")
    rv = client.post("/api/jobs", json={
        "title": "Internship Job",
        "description": "For students",
        "job_type": "internship"
    })
    job_id = rv.get_json()["id"]

    # создаём студента + отклик
    register(client, "stud2", "password", "student")
    login(client, "stud2", "password")
    rv = client.post(f"/api/jobs/{job_id}/apply", json={
        "resume_url": "http://example.com/resume.pdf",
        "cover_letter": "I am a good candidate"
    })
    assert rv.status_code == 201
    assert b"Заявка подана" in rv.data
