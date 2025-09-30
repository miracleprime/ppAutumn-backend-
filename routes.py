from flask import Flask, jsonify, request, url_for, session, render_template, redirect, Blueprint
from flask_cors import CORS
from models import db, User, Job, Application
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

routes_bp = Blueprint('routes', __name__)
CORS(routes_bp, resources={r"/*": {"origins": "*"}})


# -------------------------------
# ВАКАНСИИ (Job)
# -------------------------------
@routes_bp.route('/api/jobs', methods=['GET', 'POST'])
def jobs():
    if request.method == 'GET':
        job_type = request.args.get('job_type')
        status = request.args.get('status', 'open')
        keyword = request.args.get('q')

        query = Job.query.filter_by(status=status)
        if job_type:
            query = query.filter_by(job_type=job_type)
        if keyword:
            query = query.filter(
                (Job.title.ilike(f"%{keyword}%")) |
                (Job.description.ilike(f"%{keyword}%"))
            )

        jobs = query.all()

        job_list = []
        for job in jobs:
            job_list.append({
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'job_type': job.job_type,
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'employer': job.employer.username if job.employer else None
            })

        return jsonify(job_list)

    elif request.method == 'POST':
        if 'username' not in session:
            return jsonify({'error': 'Необходима авторизация'}), 401

        user = User.query.filter_by(username=session['username']).first()
        if not user or user.role != "employer":
            return jsonify({'error': 'Только работодатель может создавать вакансии'}), 403

        data = request.get_json()
        new_job = Job(
            title=data.get('title'),
            description=data.get('description'),
            job_type=data.get('job_type', 'internship'),
            employer=user
        )
        db.session.add(new_job)
        db.session.commit()
        return jsonify({'message': 'Вакансия создана', 'id': new_job.id}), 201


@routes_bp.route('/api/jobs/<int:job_id>', methods=['GET', 'DELETE', 'PUT'])
def job_actions(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'error': 'Вакансия не найдена'}), 404

    # --- GET ---
    if request.method == 'GET':
        return jsonify({
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'job_type': job.job_type,
            'status': job.status,
            'created_at': job.created_at.isoformat(),
            'employer': job.employer.username if job.employer else None
        })

    # --- DELETE ---
    elif request.method == 'DELETE':
        if 'username' not in session:
            return jsonify({'error': 'Необходима авторизация'}), 401

        user = User.query.filter_by(username=session['username']).first()
        if not user or user.role != "employer" or job.employer_id != user.id:
            return jsonify({'error': 'Удалять может только работодатель свою вакансию'}), 403

        db.session.delete(job)
        db.session.commit()
        return jsonify({'message': 'Вакансия удалена'})

    # --- PUT (редактирование) ---
    elif request.method == 'PUT':
        if 'username' not in session:
            return jsonify({'error': 'Необходима авторизация'}), 401

        user = User.query.filter_by(username=session['username']).first()
        if not user or user.role != "employer" or job.employer_id != user.id:
            return jsonify({'error': 'Редактировать может только работодатель свою вакансию'}), 403

        data = request.get_json()
        job.title = data.get('title', job.title)
        job.description = data.get('description', job.description)
        job.job_type = data.get('job_type', job.job_type)

        db.session.commit()
        return jsonify({'message': 'Вакансия обновлена'})



# -------------------------------
# ОТКЛИКИ (Application)
# -------------------------------
@routes_bp.route('/api/jobs/<int:job_id>/apply', methods=['POST'])
def apply(job_id):
    if 'username' not in session:
        return jsonify({'error': 'Необходима авторизация'}), 401

    user = User.query.filter_by(username=session['username']).first()
    if not user or user.role != "student":
        return jsonify({'error': 'Только студент может подавать заявки'}), 403

    job = Job.query.get(job_id)
    if not job:
        return jsonify({'error': 'Вакансия не найдена'}), 404

    data = request.get_json()
    new_app = Application(
        resume_url=data.get('resume_url'),
        cover_letter=data.get('cover_letter'),
        student=user,
        job=job
    )
    db.session.add(new_app)
    db.session.commit()

    return jsonify({'message': 'Заявка подана', 'application_id': new_app.id}), 201


@routes_bp.route('/api/applications', methods=['GET'])
def get_applications():
    if 'username' not in session:
        return jsonify({'error': 'Необходима авторизация'}), 401

    user = User.query.filter_by(username=session['username']).first()

    if user.role == "student":
        apps = Application.query.filter_by(student_id=user.id).all()
    elif user.role == "employer":
        jobs = Job.query.filter_by(employer_id=user.id).all()
        job_ids = [job.id for job in jobs]
        apps = Application.query.filter(Application.job_id.in_(job_ids)).all()
    else:
        apps = Application.query.all()

    app_list = []
    for app in apps:
        app_list.append({
            'id': app.id,
            'job_id': app.job_id,
            'job_title': app.job.title if app.job else None,
            #  студент
            'student': app.student.username if app.student else None,
            'student_full_name': app.student.full_name if app.student else "",
            'student_course': app.student.course if app.student else "",
            'student_faculty': app.student.faculty if app.student else "",
            #  работодатель (берём у вакансии -> employer -> organization)
            'organization': app.job.employer.organization if app.job and app.job.employer else "",
            'resume_url': app.resume_url,
            'cover_letter': app.cover_letter,
            'status': app.status,
            'applied_at': app.applied_at.isoformat(),
            'can_manage': (user.role == "employer")
        })

    return jsonify(app_list)


# -------------------------------
# ОБНОВЛЕНИЕ СТАТУСА ЗАЯВКИ
# -------------------------------
@routes_bp.route('/api/applications/<int:app_id>', methods=['PUT'])
def update_application(app_id):
    if 'username' not in session:
        return jsonify({'error': 'Необходима авторизация'}), 401

    user = User.query.filter_by(username=session['username']).first()
    app = Application.query.get(app_id)
    if not app:
        return jsonify({'error': 'Заявка не найдена'}), 404

    # Только работодатель может менять статус у своих заявок
    if user.role != "employer" or app.job.employer_id != user.id:
        return jsonify({'error': 'Изменять статус может только работодатель своей вакансии'}), 403

    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ["submitted", "in_review", "invited", "rejected", "accepted"]:
        return jsonify({'error': 'Недопустимый статус'}), 400

    app.status = new_status
    db.session.commit()
    return jsonify({'message': 'Статус обновлён'})

# -------------------------------
# ПРОФИЛЬ
# -------------------------------
@routes_bp.route("/api/profile", methods=["GET", "PUT"])
def api_profile():
    if "username" not in session:
        return jsonify({"error": "Необходима авторизация"}), 401

    user = User.query.filter_by(username=session["username"]).first()

    if request.method == "GET":
        return jsonify({
            "username": user.username,
            "role": user.role,
            "full_name": user.full_name,
            "course": user.course,
            "faculty": user.faculty,
            "organization": user.organization
        })

    if request.method == "PUT":
        data = request.get_json()
        if user.role == "student":
            user.full_name = data.get("full_name", user.full_name)
            user.course = data.get("course", user.course)
            user.faculty = data.get("faculty", user.faculty)
        elif user.role == "employer":
            user.organization = data.get("organization", user.organization)

        db.session.commit()
        return jsonify({"message": "Профиль обновлён"})



# -------------------------------
# РЕГИСТРАЦИЯ / ЛОГИН / ЛОГАУТ
# -------------------------------
@routes_bp.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'student')

        if not username or not password:
            error = 'Заполните все поля'
        else:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                error = 'Пользователь уже существует'
            else:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, password=hashed_password, role=role)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('routes.login'))

    return render_template('register.html', error=error)


@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('routes.index'))
        else:
            return render_template('login.html', error='Неверный логин или пароль')

    return render_template('login.html')


@routes_bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('routes.login'))


# -------------------------------
# ГЛАВНАЯ
# -------------------------------
@routes_bp.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    else:
        return redirect(url_for('routes.login'))

# -------------------------------
# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# -------------------------------
