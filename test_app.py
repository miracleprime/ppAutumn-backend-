import pytest
from app import app, db
from models import User, Job, Application

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # БД в памяти
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

# 1. Регистрация пользователя
def test_register_user(client):
    response = client.post("/register", data={"username": "stud1", "password": "123456", "role": "student"})
    assert response.status_code in (200, 302)  # redirect на login

# 2. Логин (неверный пароль)
def test_login_wrong_password(client):
    u = User(username="stud2")
    u.set_password("123456")
    db.session.add(u)
    db.session.commit()

    response = client.post("/login", data={"username": "stud2", "password": "wrong"})
    assert b"Неверный логин или пароль" in response.data

# 3. Создание вакансии (работодатель)
def test_create_job(client):
    # создаём работодателя
    u = User(username="emp1", role="employer")
    u.set_password("123456")
    db.session.add(u)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["username"] = "emp1"

    response = client.post("/api/jobs", json={
        "title": "Ассистент по математике",
        "description": "Помощь в проведении занятий",
        "job_type": "assistant"
    })
    assert response.status_code == 201

# 4. Ошибка при создании вакансии студентом
# 4. Ошибка при создании вакансии студентом
def test_student_cannot_create_job(client):
    u = User(username="stud3", role="student")
    u.set_password("123456")
    db.session.add(u)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["username"] = "stud3"

    response = client.post("/api/jobs", json={
        "title": "Фейковая вакансия",
        "description": "Не должна создаться"
    })
    assert response.status_code == 403

# 5. Получение списка вакансий
def test_get_jobs(client):
    u = User(username="emp2", role="employer")
    u.set_password("123456")
    db.session.add(u)
    db.session.commit()
    job = Job(title="Research intern", description="Лаборатория", job_type="research", employer=u)
    db.session.add(job)
    db.session.commit()

    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert b"Research intern" in response.data

# 6. Подача заявки студентом
def test_apply_to_job(client):
    emp = User(username="emp3", role="employer")
    emp.set_password("123456")
    stud = User(username="stud4", role="student")
    stud.set_password("123456")
    db.session.add_all([emp, stud])
    db.session.commit()

    job = Job(title="Internship", description="Тест", job_type="internship", employer=emp)
    db.session.add(job)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["username"] = "stud4"

    response = client.post(f"/api/jobs/{job.id}/apply", json={
        "resume_url": "http://cv.example.com/stud4.pdf",
        "cover_letter": "Хочу на стажировку"
    })
    assert response.status_code == 201

# 7. Ошибка подачи заявки работодателем
def test_employer_cannot_apply(client):
    emp = User(username="emp4", role="employer")
    emp.set_password("123456")
    db.session.add(emp)
    db.session.commit()

    job = Job(title="Internship 2", description="Тест", job_type="internship", employer=emp)
    db.session.add(job)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["username"] = "emp4"

    response = client.post(f"/api/jobs/{job.id}/apply", json={
        "resume_url": "http://cv.example.com/x.pdf",
        "cover_letter": "я работодатель"
    })
    assert response.status_code == 403
