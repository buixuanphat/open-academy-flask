from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import User, UserRole
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role_str = request.form.get('role')

        # Kiểm tra email tồn tại
        if User.query.filter_by(email=email).first():
            flash('Email này đã được đăng ký!', 'danger')
            return redirect(url_for('auth.register'))

        # Mã hóa mật khẩu
        hashed_pw = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_pw,
            role=UserRole[role_str] if role_str in UserRole.__members__ else UserRole.STUDENT
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Đăng ký thành công! Mời bạn đăng nhập.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        # Giả sử bạn dùng check_password_hash hoặc so sánh trực tiếp
        if user and (user.password_hash == password):  # Thay bằng hàm hash nếu có
            login_user(user)
            flash(f"Chào mừng trở lại, {user.username}!", "success")

            # --- PHẦN CẬP NHẬT: ĐIỀU HƯỚNG THEO ROLE ---
            if user.role.value == "instructor":
                return redirect(url_for('instructor.dashboard'))
            elif user.role.value == "admin":
                return redirect(url_for('admin.manage_users'))  # Nếu bạn có trang admin

            # Mặc định cho Student hoặc các role khác
            return redirect(url_for('student.course_list'))

        flash("Sai tài khoản hoặc mật khẩu.", "danger")
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('student.index'))