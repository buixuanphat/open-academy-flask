from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import User, Course, Enrollment, Category, UserRole, CourseStatus
from app import db
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.security import generate_password_hash
from sqlalchemy import extract

admin_bp = Blueprint('admin_custom', __name__, url_prefix='/admin')


# ==========================================
# 1. MIDDLEWARE & CONFIG
# ==========================================
@admin_bp.before_request
@login_required
def restrict_admin_access():
    if current_user.role != UserRole.ADMIN:
        flash("Bạn không có quyền truy cập vào khu vực Admin.")
        return redirect(url_for('student.index'))


# ==========================================
# 2. DASHBOARD
# ==========================================
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # 1. Thống kê tổng quan (Stats Cards)
    stats = {
        'total_users': User.query.count(),
        'total_courses': Course.query.count(),
        'total_enrollments': Enrollment.query.count(),
        'total_revenue': db.session.query(func.sum(Enrollment.total_payment)).scalar() or 0
    }

    # 2. Dữ liệu biểu đồ: Doanh thu theo tháng (Năm hiện tại)
    current_year = 2026
    monthly_revenue_raw = db.session.query(
        extract('month', Enrollment.created_date).label('month'),
        func.sum(Enrollment.total_payment).label('revenue')
    ).filter(extract('year', Enrollment.created_date) == current_year)\
     .group_by('month').order_by('month').all()

    # Chuẩn bị dữ liệu cho Chart.js (đảm bảo đủ 12 tháng)
    revenue_data = [0] * 12
    for month, rev in monthly_revenue_raw:
        revenue_data[int(month)-1] = float(rev)

    # 3. Dữ liệu biểu đồ: Khóa học theo danh mục
    course_by_cate = db.session.query(Category.name, func.count(Course.id)) \
        .join(Course).group_by(Category.name).all()
    cate_labels = [item[0] for item in course_by_cate]
    cate_data = [item[1] for item in course_by_cate]

    # 4. Top 5 khóa học được mua nhiều nhất
    top_courses = db.session.query(
        Course.title,
        func.count(Enrollment.id).label('enroll_count')
    ).join(Enrollment).group_by(Course.id)\
     .order_by(func.count(Enrollment.id).desc()).limit(5).all()

    # 5. Giảng viên mới chờ duyệt (Status Pending)
    from app.models import Status, Lecturer
    pending_lecturers = Lecturer.query.filter_by(status=Status.PENDING).limit(5).all()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           revenue_data=revenue_data,  # Dữ liệu doanh thu 12 tháng
                           labels=cate_labels,  # <--- QUAN TRỌNG: Đặt tên là labels
                           data=cate_data,  # <--- QUAN TRỌNG: Đặt tên là data
                           top_courses=top_courses,
                           pending_lecturers=pending_lecturers)

# ==========================================
# 3. QUẢN LÝ NGƯỜI DÙNG (USERS)
# ==========================================
@admin_bp.route('/users')
@login_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        role_val = request.form.get('role')

        if User.query.filter_by(email=email).first():
            flash("Email này đã tồn tại!")
            return redirect(url_for('admin_custom.add_user'))

        hashed_pw = generate_password_hash(password)
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_pw,
            role=UserRole(role_val)
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Thêm người dùng thành công!")
        return redirect(url_for('admin_custom.manage_users'))

    return render_template('admin/user_form.html', user=None)


@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.role = UserRole(request.form.get('role'))

        new_password = request.form.get('password')
        if new_password:
            user.password = generate_password_hash(new_password)

        db.session.commit()
        flash("Cập nhật thông tin thành công!")
        return redirect(url_for('admin_custom.manage_users'))

    return render_template('admin/user_form.html', user=user)


@admin_bp.route('/users/toggle/<int:user_id>')
@login_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Bạn không thể tự khóa chính mình!")
    else:
        user.active = not user.active
        db.session.commit()
        status = "mở" if user.active else "khóa"
        flash(f"Đã {status} tài khoản {user.email}")
    return redirect(url_for('admin_custom.manage_users'))


@admin_bp.route('/users/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Không thể tự xóa chính mình!")
    else:
        db.session.delete(user)
        db.session.commit()
        flash("Đã xóa người dùng.")
    return redirect(url_for('admin_custom.manage_users'))


# ==========================================
# 4. QUẢN LÝ KHÓA HỌC (COURSES)
# ==========================================
@admin_bp.route('/courses')
@login_required
def manage_courses():
    courses = Course.query.all()
    return render_template('admin/courses.html', courses=courses)


@admin_bp.route('/courses/detail/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    sections_data = []
    for section in course.sections:
        lessons = [{"title": l.title, "order": l.order_index} for l in section.lessons]
        sections_data.append({
            "title": section.title,
            "lessons": lessons
        })

    return {
        "title": course.title,
        "description": course.description,
        "price": f"{course.price:,.0f} đ",
        "lecturer": f"{course.lecturer.last_name} {course.lecturer.first_name}",
        "sections": sections_data
    }


@admin_bp.route('/courses/approve/<int:course_id>')
@login_required
def approve_course(course_id):
    course = Course.query.get_or_404(course_id)
    course.status = CourseStatus.ACTIVE
    db.session.commit()
    flash(f"Đã duyệt khóa học: {course.title}")
    return redirect(url_for('admin_custom.manage_courses'))

@admin_bp.route('/courses/delete/<int:course_id>')
@login_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    # Lưu lại tiêu đề để hiển thị thông báo flash
    title = course.title
    db.session.delete(course)
    db.session.commit()
    flash(f"Đã xóa khóa học: {title}")
    return redirect(url_for('admin_custom.manage_courses'))
