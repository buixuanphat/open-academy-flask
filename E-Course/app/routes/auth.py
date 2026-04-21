from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Student, Lecturer, UserRole, StudyGoal, StudentLevel, Status
from app import db

bp = Blueprint('auth', __name__)



@bp.route('/login', methods=['GET', 'POST'])
def login():
    # 1. Nếu đã đăng nhập rồi, điều hướng dựa trên vai trò
    if current_user.is_authenticated:
        return redirect_by_role(current_user)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.active:
                flash('Tài khoản của bạn đã bị khóa!')
                return redirect(url_for('auth.login'))

            login_user(user)
            return redirect_by_role(user)

        flash('Email hoặc mật khẩu không đúng!')

    return render_template('auth/login.html')


# Hàm bổ trợ để điều hướng người dùng dựa trên vai trò (Tránh lặp code)
def redirect_by_role(user):
    if user.role == UserRole.ADMIN:
        return redirect(url_for('admin_custom.dashboard'))
    elif user.role == UserRole.LECTURER:
        return redirect(url_for('lecturer.dashboard'))
    return redirect(url_for('student.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    # (Giữ nguyên logic cũ của bạn, nhưng lưu ý: Thường không cho phép đăng ký Admin công khai)
    if request.method == 'POST':
        email = request.form.get('email')
        role_str = request.form.get('role')  # 'lecturer' hoặc 'student'

        if User.query.filter_by(email=email).first():
            flash('Email đã tồn tại!')
            return redirect(url_for('auth.register'))

        password_hash = generate_password_hash(request.form.get('password'))

        if role_str == 'lecturer':
            new_user = Lecturer(
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                email=email,
                password=password_hash,
                role=UserRole.LECTURER,  # Enum
                bio="Chưa có tiểu sử.",
                status=Status.PENDING
            )
        else:
            new_user = Student(
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                email=email,
                password=password_hash,
                role=UserRole.STUDENT,  # Enum
                goal=StudyGoal.UPSKILL,
                level=StudentLevel.BEGINNER
            )

        db.session.add(new_user)
        db.session.commit()
        flash('Đăng ký thành công! Hãy đăng nhập.')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))