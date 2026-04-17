from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Course, Enrollment, Rating, Category, db, CourseStatus,Lesson,StudyGoal, StudentLevel
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader

lecturer_bp = Blueprint('lecturer', __name__, url_prefix='/lecturer')


@lecturer_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role.value != 'lecturer':
        flash("Bạn không có quyền truy cập trang này.", "danger")
        return redirect(url_for('student.index'))

    # Lấy danh sách khóa học của giảng viên này
    page = request.args.get('page', 1, type=int)
    courses_query = Course.query.filter_by(lecturer_id=current_user.id).order_by(Course.created_date.desc())
    pagination = courses_query.paginate(page=page, per_page=5)

    # Thống kê tổng quan
    total_courses = courses_query.count()
    active_courses = Course.query.filter_by(lecturer_id=current_user.id, status=CourseStatus.ACTIVE).count()

    # Tổng học viên (tất cả khóa học của giảng viên này)
    total_students = db.session.query(Enrollment).join(Course).filter(Course.lecturer_id == current_user.id).count()

    return render_template('lecturer/dashboard.html',
                           pagination=pagination,
                           total_courses=total_courses,
                           active_courses=active_courses,
                           total_students=total_students)


@lecturer_bp.route('/course/create', methods=['GET', 'POST'])
@login_required
def create_course():
    if request.method == 'POST':
        # 1. Lấy thông tin từ Form
        title = request.form.get('title')
        description = request.form.get('description')
        raw_price = request.form.get('price')
        price = float(raw_price) if raw_price and raw_price.strip() else 0.0
        category_id = int(request.form.get('category_id'))
        goal = request.form.get('goal')
        level = request.form.get('level')

        # 2. Xử lý upload ảnh bìa lên Cloudinary
        file = request.files.get('image')
        image_url = "https://via.placeholder.com/500x300"  # Ảnh mặc định nếu không upload

        if file and file.filename != '':
            upload_result = cloudinary.uploader.upload(
                file,
                folder="e_course/thumbnails",
                public_id=f"course_{current_user.id}_{int(datetime.now().timestamp())}"
            )
            image_url = upload_result.get('secure_url')

        # 3. Lưu vào Database
        try:
            new_course = Course(
                title=title,
                description=description,
                price=price,
                category_id=category_id,
                lecturer_id=current_user.id,
                goal=goal,
                level=level,
                image=image_url,
                status=CourseStatus.DRAFT  # Mặc định là bản nháp
            )
            db.session.add(new_course)
            db.session.commit()
            flash("Đã tạo khóa học thành công! Hãy tiếp tục thêm nội dung bài học.", "success")
            return redirect(url_for('lecturer.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Có lỗi xảy ra: {str(e)}", "danger")

    categories = Category.query.all()
    # Truyền các Enum để hiển thị trong Select Box
    return render_template('lecturer/create_course.html',
                           categories=categories,
                           goals=StudyGoal,
                           levels=StudentLevel)


@lecturer_bp.route('/course/<int:course_id>/add-lesson', methods=['POST'])
@login_required
def add_lesson(course_id):
    video_file = request.files.get('video')
    video_url = ""

    if video_file:
        # Upload Video lên Cloudinary (chỉ định resource_type="video")
        upload_result = cloudinary.uploader.upload(
            video_file,
            resource_type="video",
            folder="e_course/lessons"
        )
        video_url = upload_result.get('secure_url')

    new_lesson = Lesson(
        title=request.form.get('title'),
        content=request.form.get('content'),
        video=video_url,
        order_index=request.form.get('order_index'),
        section_id=request.form.get('section_id')
    )
    db.session.add(new_lesson)
    db.session.commit()
    flash("Thêm bài học thành công!", "success")
    return redirect(url_for('lecturer.edit_course', course_id=course_id))