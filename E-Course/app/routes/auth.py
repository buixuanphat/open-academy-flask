from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, Student, Lecturer, UserRole, StudyGoal, StudentLevel, Status
from app import db

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role.value == 'lecturer':
            return redirect(url_for('lecturer.dashboard'))
        return redirect(url_for('student.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        # Trong hàm login:
        if user and check_password_hash(user.password, password):
            login_user(user)
            # Đồng bộ: Nếu là giảng viên thì cho vào dashboard, còn lại về index student
            if user.role.value == 'lecturer':
                return redirect(url_for('lecturer.dashboard'))
            return redirect(url_for('student.index'))
        flash('Email hoặc mật khẩu không đúng!')

    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        role = request.form.get('role')

        if User.query.filter_by(email=email).first():
            flash('Email đã tồn tại!')
            return redirect(url_for('auth.register'))

        password_hash = generate_password_hash(request.form.get('password'))

        # Khởi tạo dữ liệu dựa trên vai trò
        if role == 'lecturer':
            new_user = Lecturer(
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                email=email,
                password=password_hash,
                role=UserRole.LECTURER,
                bio="Chưa có tiểu sử.",
                status=Status.PENDING
            )
        else:
            new_user = Student(
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                email=email,
                password=password_hash,
                role=UserRole.STUDENT,
                goal=StudyGoal.UPSKILL,  # Giá trị mặc định
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