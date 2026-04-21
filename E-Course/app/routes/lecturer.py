from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Course, Enrollment, Rating,UserRole, Category, db, CourseStatus,Lesson,StudyGoal, StudentLevel,Section
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from sqlalchemy import func

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


@lecturer_bp.route('/course/<int:course_id>/lesson/add', methods=['POST'])
@login_required
def add_lesson(course_id):
    section_id = request.form.get('section_id')
    video_file = request.files.get('video')
    video_url = ""

    if video_file:
        # Lưu ý: Upload video có thể mất thời gian
        upload_result = cloudinary.uploader.upload(
            video_file,
            resource_type="video",
            folder=f"e_course/course_{course_id}/lessons"
        )
        video_url = upload_result.get('secure_url')

    new_lesson = Lesson(
        title=request.form.get('title'),
        content=request.form.get('content'),
        video=video_url,
        section_id=section_id,
        order_index=1 # Bạn có thể cải tiến phần này để tự tăng index
    )
    db.session.add(new_lesson)
    db.session.commit()
    flash("Bài học đã được tải lên thành công!", "success")
    return redirect(url_for('lecturer.manage_course', course_id=course_id))


@lecturer_bp.route('/course/<int:course_id>/manage')
@login_required
def manage_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.lecturer_id != current_user.id:
        flash("Bạn không có quyền quản lý khóa học này.", "danger")
        return redirect(url_for('lecturer.dashboard'))

    # Lấy danh sách các chương của khóa học này
    sections = Section.query.filter_by(course_id=course_id).order_by(Section.id.asc()).all()
    return render_template('lecturer/manage_course.html', course=course, sections=sections)


@lecturer_bp.route('/course/<int:course_id>/section/add', methods=['POST'])
@login_required
def add_section(course_id):
    # Lấy giá trị từ ô input có name="name" trong HTML
    section_name_from_form = request.form.get('name')

    if section_name_from_form:
        # Sửa name= thành title= để khớp với Model Section
        new_section = Section(
            title=section_name_from_form,
            course_id=course_id
        )
        db.session.add(new_section)
        db.session.commit()
        flash("Đã thêm chương mới thành công!", "success")
    else:
        flash("Vui lòng nhập tên chương!", "warning")

    return redirect(url_for('lecturer.manage_course', course_id=course_id))


# --- QUẢN LÝ SECTION (CHƯƠNG) ---

@lecturer_bp.route('/section/<int:section_id>/delete', methods=['POST'])
@login_required
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)
    course_id = section.course_id
    # Kiểm tra quyền chủ sở hữu
    if section.course.lecturer_id != current_user.id:
        return "Không có quyền", 403

    db.session.delete(section)
    db.session.commit()
    flash("Đã xóa chương và các bài học liên quan.", "success")
    return redirect(url_for('lecturer.manage_course', course_id=course_id))


# --- QUẢN LÝ LESSON (BÀI HỌC) ---

@lecturer_bp.route('/lesson/<int:lesson_id>/delete', methods=['POST'])
@login_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.section.course_id
    if lesson.section.course.lecturer_id != current_user.id:
        return "Không có quyền", 403

    db.session.delete(lesson)
    db.session.commit()
    flash("Đã xóa bài học thành công.", "success")
    return redirect(url_for('lecturer.manage_course', course_id=course_id))


# Sửa tên Chương
@lecturer_bp.route('/section/<int:section_id>/edit', methods=['POST'])
@login_required
def edit_section(section_id):
    section = Section.query.get_or_404(section_id)
    if section.course.lecturer_id != current_user.id:
        return "Không có quyền", 403

    new_title = request.form.get('title')
    if new_title:
        section.title = new_title
        db.session.commit()
        flash("Đã cập nhật tên chương!", "success")
    return redirect(url_for('lecturer.manage_course', course_id=section.course_id))


# Sửa thông tin Bài học
@lecturer_bp.route('/lesson/<int:lesson_id>/edit', methods=['POST'])
@login_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.section.course.lecturer_id != current_user.id:
        return "Không có quyền", 403

    lesson.title = request.form.get('title')
    lesson.content = request.form.get('content')

    # Nếu có upload video mới thì mới cập nhật video
    video_file = request.files.get('video')
    if video_file and video_file.filename != '':
        upload_result = cloudinary.uploader.upload(video_file, resource_type="video", folder="e_course/lessons")
        lesson.video = upload_result.get('secure_url')

    db.session.commit()
    flash("Đã cập nhật bài học!", "success")
    return redirect(url_for('lecturer.manage_course', course_id=lesson.section.course_id))


@lecturer_bp.route('/statistics')
@login_required
def statistics():
    if current_user.role != UserRole.LECTURER:
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('student.index'))

    # Lấy danh sách khóa học dựa trên lecturer_id
    courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    return render_template('lecturer/statistics.html', courses=courses)

@lecturer_bp.route('/statistics/course/<int:course_id>')
@login_required
def course_statistics(course_id):
    course = Course.query.get_or_404(course_id)

    if course.lecturer_id != current_user.id:
        flash('Bạn không có quyền xem thống kê khóa học này.', 'danger')
        return redirect(url_for('lecturer.statistics'))

    # 1. Đếm học viên
    total_students = Enrollment.query.filter_by(course_id=course_id).count()

    # 2. Tính doanh thu
    total_revenue = total_students * (course.price or 0)

    # 3. Tính đánh giá trung bình dựa trên cột .score
    avg_rating = db.session.query(func.avg(Rating.score)).filter(Rating.course_id == course_id).scalar() or 0
    avg_rating = round(float(avg_rating), 1)

    return render_template('lecturer/course_stats_detail.html',
                           course=course,
                           total_students=total_students,
                           total_revenue=total_revenue,
                           avg_rating=avg_rating)