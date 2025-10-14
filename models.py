from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "student" или "employer"

    # Дополнительные поля для профиля
    full_name = db.Column(db.String(150))
    course = db.Column(db.String(50))
    faculty = db.Column(db.String(100))
    organization = db.Column(db.String(150))

    # Связи
    jobs = db.relationship("Job", back_populates="employer", cascade="all, delete-orphan")
    applications = db.relationship("Application", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}, role={self.role}>"


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    job_type = db.Column(db.String(50), default="internship")
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    employer = db.relationship("User", back_populates="jobs")

    applications = db.relationship("Application", back_populates="job", cascade="all, delete-orphan")

    # ⚡ Переименовываем колонку, чтобы не конфликтовала со старой таблицей rating
    job_rating = db.Column("job_rating", db.Float, default=None)

    def __repr__(self):
        return f"<Job {self.title}, rating={self.job_rating}>"



class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resume_url = db.Column(db.String(250))
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(20), default="submitted")
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    student = db.relationship("User", back_populates="applications")

    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    job = db.relationship("Job", back_populates="applications")

    rating = db.Column(db.Integer, nullable=True)  # ⭐ Новое поле — оценка стажировки

    def __repr__(self):
        return f"<Application job_id={self.job_id}, student_id={self.student_id}, rating={self.rating}>"

