from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Course, Category, Section, Lesson, UserRole, Enrollment, LessonProgress
from app import db
from functools import wraps
import cloudinary.uploader
from sqlalchemy import func

instructor_bp = Blueprint('instructor', __name__)


# Decorator kiểm tra quyền giảng viên
def instructor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != UserRole.INSTRUCTOR:
            flash("Bạn không có quyền truy cập trang này.", "danger")
            return redirect(url_for('student.course_list'))
        return f(*args, **kwargs)

    return decorated_function


@instructor_bp.route('/instructor/dashboard')
@login_required
@instructor_required
def dashboard():
    # --- PHẦN 1: TÍNH TOÁN THỐNG KÊ ---
    # 1. Lấy danh sách ID các khóa học của giảng viên này
    user_course_ids = [c.id for c in Course.query.filter_by(instructor_id=current_user.id).all()]

    # 2. Tổng số học viên (Đếm số bản ghi Enrollment của các khóa học trên)
    total_students = Enrollment.query.filter(Enrollment.course_id.in_(user_course_ids)).count()

    # 3. Tổng doanh thu (Sum cột paid_amount của các Enrollment đã thanh toán)
    total_revenue = db.session.query(func.sum(Enrollment.paid_amount)) \
                        .filter(Enrollment.course_id.in_(user_course_ids), Enrollment.payment_status == True) \
                        .scalar() or 0

    # 4. Số lượng khóa học hiện có
    total_courses = len(user_course_ids)

    # --- PHẦN 2: BỘ LỌC & DANH SÁCH (Giữ nguyên logic cũ) ---
    q = request.args.get('q', '')
    category_id = request.args.get('category_id', '')
    query = Course.query.filter_by(instructor_id=current_user.id)
    if q:
        query = query.filter(Course.title.contains(q))
    if category_id:
        query = query.filter_by(category_id=category_id)

    courses = query.all()
    categories = Category.query.all()

    return render_template('instructor/dashboard.html',
                           courses=courses,
                           categories=categories,
                           q=q,
                           current_category=category_id,
                           total_students=total_students,
                           total_revenue=total_revenue,
                           total_courses=total_courses)


@instructor_bp.route('/instructor/course/create', methods=['GET', 'POST'])
@login_required
@instructor_required
def create_course():
    # Lấy danh sách danh mục để hiện trong thẻ <select>
    categories = Category.query.all()

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = request.form.get('price')
        category_id = request.form.get('category_id')
        thumbnail = request.files.get('thumbnail')

        image_url = ""
        # 1. Upload ảnh bìa lên Cloudinary (nếu có)
        if thumbnail and thumbnail.filename != '':
            upload_result = cloudinary.uploader.upload(
                thumbnail,
                folder="e-course/thumbnails/"
            )
            image_url = upload_result.get('secure_url')

        # 2. Lưu vào Database
        new_course = Course(
            title=title,
            description=description,
            price=float(price) if price else 0.0,
            image_url=image_url,
            category_id=category_id,
            instructor_id=current_user.id
        )

        db.session.add(new_course)
        db.session.commit()

        flash("Tạo khóa học thành công! Hãy thêm nội dung cho khóa học.", "success")
        return redirect(url_for('instructor.manage_content', course_id=new_course.id))

    return render_template('instructor/create_course.html', categories=categories)

@instructor_bp.route('/instructor/course/<int:course_id>/content')
@login_required
@instructor_required
def manage_content(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        return "Unauthorized", 403
    return render_template('instructor/manage_content.html', course=course)


# --- QUẢN LÝ CHƯƠNG (SECTION) ---
@instructor_bp.route('/instructor/course/<int:course_id>/section/add', methods=['POST'])
@login_required
@instructor_required
def add_section(course_id):
    course = Course.query.get_or_404(course_id)
    title = request.form.get('section_title')

    if title:
        new_section = Section(title=title, course_id=course.id)
        db.session.add(new_section)
        db.session.commit()
        flash("Đã thêm chương mới!", "success")
    return redirect(url_for('instructor.manage_content', course_id=course.id))


# --- QUẢN LÝ BÀI HỌC (LESSON) ---
@instructor_bp.route('/instructor/section/<int:section_id>/lesson/add', methods=['POST'])
@login_required
@instructor_required
def add_lesson(section_id):
    section = Section.query.get_or_404(section_id)
    title = request.form.get('lesson_title')
    lesson_type = request.form.get('lesson_type')

    video_url = ""

    # Kiểm tra nếu người dùng upload file video
    if 'video_file' in request.files:
        file_to_upload = request.files['video_file']
        if file_to_upload.filename != '':
            # Upload lên Cloudinary với resource_type='video'
            # Sửa từ cloudinary.uploader.upload_video thành cloudinary.uploader.upload
            upload_result = cloudinary.uploader.upload(
                file_to_upload,
                folder="e-course/lessons/",
                resource_type="video"  # Đây là tham số quan trọng để Cloudinary hiểu đây là video
            )
            # Lấy URL bảo mật (https) trả về
            video_url = upload_result.get('secure_url')

    if title:
        current_count = Lesson.query.filter_by(section_id=section_id).count()
        new_lesson = Lesson(
            title=title,
            section_id=section_id,
            lesson_type=lesson_type,
            content_url=video_url,  # Lưu link từ Cloudinary vào đây
            order=current_count + 1
        )
        db.session.add(new_lesson)
        db.session.commit()
        flash("Tải lên video bài học thành công!", "success")

    return redirect(url_for('instructor.manage_content', course_id=section.course_id))


# ==================== QUẢN LÝ CHƯƠNG (SECTION) ====================

@instructor_bp.route('/instructor/section/<int:section_id>/edit', methods=['POST'])
@login_required
@instructor_required
def edit_section(section_id):
    section = Section.query.get_or_404(section_id)
    new_title = request.form.get('section_title')
    if new_title:
        section.title = new_title
        db.session.commit()
        flash("Cập nhật tên chương thành công!", "success")
    return redirect(url_for('instructor.manage_content', course_id=section.course_id))


@instructor_bp.route('/instructor/section/<int:section_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)
    course_id = section.course_id
    db.session.delete(section)
    db.session.commit()
    flash("Đã xóa chương và các bài học liên quan!", "warning")
    return redirect(url_for('instructor.manage_content', course_id=course_id))


# ==================== QUẢN LÝ BÀI HỌC (LESSON) ====================

@instructor_bp.route('/instructor/lesson/<int:lesson_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.section.course_id

    # Lưu ý: Nếu muốn tiết kiệm bộ nhớ Cloudinary, bạn có thể gọi api xóa file tại đây trước khi xóa DB
    db.session.delete(lesson)
    db.session.commit()
    flash("Đã xóa bài học!", "info")
    return redirect(url_for('instructor.manage_content', course_id=course_id))


@instructor_bp.route('/instructor/course/<int:course_id>/delete', methods=['POST'])
@login_required
@instructor_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)

    # Kiểm tra bảo mật: Chỉ chủ sở hữu mới được xóa
    if course.instructor_id != current_user.id:
        flash("Bạn không có quyền xóa khóa học này!", "danger")
        return redirect(url_for('instructor.dashboard'))

    try:
        # Tùy chọn: Xóa ảnh bìa trên Cloudinary trước khi xóa trong DB
        if course.image_url:
            public_id = course.image_url.split('/')[-1].split('.')[0]
            cloudinary.uploader.destroy(f"e-course/thumbnails/{public_id}")

        db.session.delete(course)
        db.session.commit()
        flash(f"Đã xóa thành công khóa học: {course.title}", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi xóa khóa học: {str(e)}", "danger")

    return redirect(url_for('instructor.dashboard'))


@instructor_bp.route('/instructor/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@instructor_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    # Bảo mật: Chỉ chủ sở hữu mới được sửa
    if course.instructor_id != current_user.id:
        flash("Bạn không có quyền chỉnh sửa khóa học này!", "danger")
        return redirect(url_for('instructor.dashboard'))

    categories = Category.query.all()

    if request.method == 'POST':
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.price = float(request.form.get('price'))
        course.category_id = request.form.get('category_id')

        # Xử lý nếu giảng viên thay ảnh bìa mới
        thumbnail = request.files.get('thumbnail')
        if thumbnail and thumbnail.filename != '':
            # Upload ảnh mới lên Cloudinary
            upload_result = cloudinary.uploader.upload(thumbnail, folder="e-course/thumbnails/")
            course.image_url = upload_result.get('secure_url')

        db.session.commit()
        flash("Cập nhật thông tin khóa học thành công!", "success")
        return redirect(url_for('instructor.dashboard'))

    return render_template('instructor/edit_course.html', course=course, categories=categories)


@instructor_bp.route('/instructor/course/<int:course_id>/stats')
@login_required
@instructor_required
def course_stats(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        return redirect(url_for('instructor.dashboard'))

    # Lấy danh sách học viên đã đăng ký khóa này
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()

    # Tính toán tiến độ cho từng học viên
    total_lessons = Lesson.query.join(Section).filter(Section.course_id == course_id).count()

    stats_data = []
    for enr in enrollments:
        # Giả sử bạn có table LessonProgress để lưu các bài học đã hoàn thành
        completed_lessons = LessonProgress.query.filter_by(user_id=enr.user_id, is_completed=True) \
            .join(Lesson).join(Section).filter(Section.course_id == course_id).count()

        progress_percent = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

        stats_data.append({
            'student_name': enr.user.username,
            'enroll_date': enr.enrolled_at,
            'progress': round(progress_percent, 1)
        })

    return render_template('instructor/course_stats.html', course=course, stats_data=stats_data)