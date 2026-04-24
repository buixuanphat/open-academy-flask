from datetime import datetime

from flask_login import login_user, logout_user, login_required

from openacademy import app, utils, models, login, VNPAY_TMN_CODE, VNPAY_RETURN_URL, VNPAY_PAYMENT_URL, \
    VNPAY_HASH_SECRET
import cloudinary.uploader

from openacademy.models import UserRole, Course, Lesson
from openacademy.utils import add_lecturer, add_student, vnpay

from openacademy.models import Enrollment, db

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from openacademy import app, utils
from openacademy.models import Category, StudyGoal, StudentLevel, CourseStatus, Course, Section

@app.route('/')
def home():
    return render_template('login.html')


@app.route('/lecturer-register', methods=['GET', 'POST'])
def lecturer_register():
    err_msg = ""
    if request.method == 'POST':
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        bio = request.form.get('bio')

        if password != confirm_password:
            err_msg = "Mật khẩu xác nhận không khớp!"
        else:
            try:
                avatar_file = request.files.get('avatar')
                avatar_url = None
                if avatar_file:
                    res_avatar = cloudinary.uploader.upload(avatar_file)
                    avatar_url = res_avatar.get('secure_url')

                degree_files = request.files.getlist('degree_files[]')
                degree_names = request.form.getlist('degree_names[]')
                degrees_data = []

                for i in range(len(degree_files)):
                    file = degree_files[i]
                    if file and file.filename != '':
                        res_degree = cloudinary.uploader.upload(file)

                        name_val = degree_names[i].strip() if i < len(degree_names) else file.filename
                        if not name_val:
                            name_val = file.filename

                        degrees_data.append({
                            'name': name_val,
                            'url': res_degree.get('secure_url')
                        })

                new_lecturer = add_lecturer(
                    last_name=last_name,
                    first_name=first_name,
                    email=email,
                    password=password,
                    avatar=avatar_url,
                    bio=bio,
                    degrees=degrees_data
                )

                if new_lecturer:
                    return redirect(url_for('home'))
                else:
                    err_msg = "Có lỗi xảy ra"

            except Exception as e:
                err_msg = f"Lỗi hệ thống: {str(e)}"

    return render_template('lecturer_register.html', err_msg=err_msg)


@app.route('/student-register', methods=['GET', 'POST'])
def student_register():
    err_msg = ""
    if request.method == 'POST':
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        goal = request.form.get('goal')
        level = request.form.get('level')

        if password != confirm_password:
            err_msg = "Mật khẩu xác nhận không khớp!"
        else:
            try:
                avatar_file = request.files.get('avatar')
                avatar_url = None
                if avatar_file:
                    res_avatar = cloudinary.uploader.upload(avatar_file)
                    avatar_url = res_avatar.get('secure_url')

                new_student = add_student(
                    last_name=last_name,
                    first_name=first_name,
                    email=email,
                    password=password,
                    avatar=avatar_url,
                    goal=goal,
                    level=level
                )

                if new_student:
                    return redirect(url_for('home'))
                else:
                    err_msg = "Có lỗi xảy ra"

            except Exception as e:
                err_msg = f"Lỗi hệ thống: {str(e)}"
    return render_template('student_register.html', goals=models.StudyGoal, levels=models.StudentLevel, err_msg=err_msg)


@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    err_msg = ''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = utils.check_login(email=email, password=password)
        if user:
            login_user(user=user)

            # Sửa logic so sánh ở đây:
            if user.role == UserRole.STUDENT:
                return redirect(url_for('load_courses'))
            elif user.role == UserRole.LECTURER:
                return redirect(url_for('lecturer_dashboard'))
            elif user.role == UserRole.ADMIN:
                return redirect('/admin')

            return redirect(url_for('home'))
        else:
            err_msg = 'Email hoặc mật khẩu không chính xác'

    return render_template('login.html', err_msg=err_msg)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/courses', methods=['GET'])
def load_courses():
    # 1. Lấy tham số tìm kiếm từ URL
    kw = request.args.get('kw')
    category_id = request.args.get('category_id')
    lecturer_id = request.args.get('lecturer_id')
    goal = request.args.get('goal')
    level = request.args.get('level')

    # 2. Load danh sách khóa học theo bộ lọc
    courses = utils.load_courses(kw, category_id, lecturer_id, goal, level)
    categories = utils.load_categories()
    lecturers = utils.load_lecturers()

    # 3. Logic gợi ý thông minh
    recommended_courses = []
    # Chỉ gợi ý cho Student đã đăng nhập và khi không có tham số tìm kiếm nào
    if current_user.is_authenticated and current_user.role == UserRole.STUDENT:
        if not any([kw, category_id, lecturer_id, goal, level]):
            recommended_courses = utils.get_recommended_courses(user_id=current_user.id)

    return render_template('courses.html',
                           courses=courses,
                           recommended=recommended_courses,
                           categories=categories,
                           lecturers=lecturers,
                           goals=models.StudyGoal,
                           levels=models.StudentLevel)


@app.route('/my-courses', methods=['GET'])
def load_my_courses():
    kw = request.args.get('kw')

    courses = utils.load_my_courses(current_user.id, kw)

    return render_template('my_courses.html', courses=courses)

@app.route('/courses/<int:course_id>')
def course_detail(course_id):
    course = utils.load_course_details(course_id)
    enrolled_ids = []
    if current_user.is_authenticated:
        enrollments = utils.load_enrollments(current_user.id)
        enrolled_ids = [en.course_id for en in enrollments]

    return render_template('course_detail.html',
                           course=course,
                           enrolled_ids=enrolled_ids)


@app.route('/payment', methods=['POST'])
def payment():
    course_id = request.form.get('course_id')
    amount_str = request.form.get('amount')
    amount = int(float(amount_str))
    order_desc = request.form.get('order_desc')
    txn_ref = f"{course_id}-{datetime.now().strftime('%H%M%S')}"
    vnp = vnpay()
    vnp.request_data['vnp_TxnRef'] = txn_ref
    vnp.request_data['vnp_Version'] = '2.1.0'
    vnp.request_data['vnp_Command'] = 'pay'
    vnp.request_data['vnp_TmnCode'] = VNPAY_TMN_CODE
    vnp.request_data['vnp_Amount'] = int(amount) * 100
    vnp.request_data['vnp_CurrCode'] = 'VND'
    vnp.request_data['vnp_TxnRef'] = txn_ref
    vnp.request_data['vnp_OrderInfo'] = order_desc
    vnp.request_data['vnp_OrderType'] = 'billpayment'
    vnp.request_data['vnp_Locale'] = 'vn'
    vnp.request_data['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
    vnp.request_data['vnp_IpAddr'] = request.remote_addr
    vnp.request_data['vnp_ReturnUrl'] = VNPAY_RETURN_URL

    vnpay_payment_url = vnp.get_payment_url(VNPAY_PAYMENT_URL, VNPAY_HASH_SECRET)
    return redirect(vnpay_payment_url)


@app.route('/payment_return', methods=['GET'])
def payment_return():
    vnp = vnpay()
    vnp.response_data = request.args.to_dict()

    if vnp.validate_response(VNPAY_HASH_SECRET):
        if vnp.response_data['vnp_ResponseCode'] == '00':

            txn_ref = vnp.response_data['vnp_TxnRef']

            course_id = int(txn_ref.split('-')[0])

            vnp_amount = float(vnp.response_data['vnp_Amount']) / 100

            existing_enroll = Enrollment.query.filter_by(
                student_id=current_user.id,
                course_id=course_id
            ).first()

            if not existing_enroll:
                new_enrollment = Enrollment(
                    student_id=current_user.id,
                    course_id=course_id,
                    total_payment=vnp_amount,
                    payment_status=True
                )
                db.session.add(new_enrollment)
                db.session.commit()
                return "Chúc mừng! Bạn đã đăng ký khóa học thành công."

            return "Khóa học này bạn đã đăng ký rồi."
        else:
            return f"Thanh toán không thành công. Mã lỗi: {vnp.response_data['vnp_ResponseCode']}"
    else:
        return "Lỗi xác thực chữ ký bảo mật."


@app.route('/learning/<int:course_id>/<int:lesson_id>')
def learning(course_id, lesson_id):
    course = utils.load_course_details(course_id)
    current_lesson = Lesson.query.get_or_404(lesson_id)

    percent = utils.load_progress(current_user.id, current_lesson.id)

    progress = utils.calculate_course_progress(current_user.id, course_id)

    return render_template('learning.html', course=course, current_lesson=current_lesson, percent=percent, progress=progress)


@app.route('/update-progress', methods=['POST'])
def update_progress():
    data = request.get_json()
    lesson_id = data.get('lesson_id')
    student_id = data.get('student_id')
    percent = data.get('percent')

    utils.update_progress(student_id, lesson_id, percent)

    return {"status": "success"}, 200


@app.route('/enroll-free/<int:course_id>')
@login_required
def enroll_free(course_id):
    course = Course.query.get_or_404(course_id)

    if course.price == 0:
        msg = utils.create_enrollment(current_user.id, course_id, 0)

        if course.sections and course.sections[0].lessons:
            first_lesson_id = course.sections[0].lessons[0].id
            return redirect(url_for('learning', course_id=course.id, lesson_id=first_lesson_id))

    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/lecturer/dashboard')
@login_required
def lecturer_dashboard():
    # Sửa từ current_user.role.value != 'lecturer' thành:
    if current_user.role != UserRole.LECTURER:
        flash("Bạn không có quyền truy cập trang này!", "danger")
        return redirect(url_for('home'))

    kw = request.args.get('kw', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)

    pagination = utils.get_courses_by_lecturer(kw, status, page)
    stats = utils.get_lecturer_stats()

    return render_template('lecturer/dashboard.html',
                           pagination=pagination,
                           **stats,
                           CourseStatus=CourseStatus)


@app.route('/lecturer/course/create', methods=['GET', 'POST'])
@login_required
def create_course():
    if request.method == 'POST':
        try:
            utils.add_new_course(request.form, request.files.get('image'))
            flash("Tạo khóa học thành công!", "success")
            return redirect(url_for('lecturer_dashboard'))
        except Exception as e:
            db.session.rollback() # THÊM DÒNG NÀY
            print(f"DEBUG ERROR: {e}")
            flash(f"Lỗi hệ thống: {str(e)}", "danger")

    return render_template('lecturer/create_course.html',
                           categories=Category.query.all(),
                           goals=StudyGoal, levels=StudentLevel)


@app.route('/lecturer/course/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)

    # Kiểm tra quyền: Chỉ giảng viên tạo ra khóa học này mới được xóa
    if course.lecturer_id != current_user.id:
        flash("Bạn không có quyền xóa khóa học này!", "danger")
        return redirect(url_for('lecturer_dashboard'))

    try:
        db.session.delete(course)
        db.session.commit()
        flash("Xóa khóa học thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi khi xóa: {str(e)}", "danger")

    return redirect(url_for('lecturer_dashboard'))

@app.route('/lecturer/course/<int:course_id>/manage')
@login_required
def manage_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.lecturer_id != current_user.id:
        return "Từ chối truy cập", 403

    sections = Section.query.filter_by(course_id=course_id).all()
    return render_template('lecturer/manage_course.html', course=course, sections=sections)


@app.route('/lecturer/course/<int:course_id>/section/add', methods=['POST'])
@login_required
def add_section(course_id):
    title = request.form.get('name')
    if title:
        utils.add_section_to_course(course_id, title)
        flash("Đã thêm chương mới!", "success")
    return redirect(url_for('manage_course', course_id=course_id))


@app.route('/lecturer/course/lesson/add', methods=['POST'])
@login_required
def add_lesson():
    # Lấy course_id từ form để redirect về đúng trang quản lý
    course_id = request.form.get('course_id')
    try:
        utils.add_lesson_to_section(request.form, request.files.get('video'))
        flash("Thêm bài học thành công!", "success")
    except Exception as e:
        flash(f"Lỗi: {str(e)}", "danger")
    return redirect(url_for('manage_course', course_id=course_id))


@app.route('/lecturer/section/<int:section_id>/delete', methods=['POST'])
@login_required
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)
    course_id = section.course_id
    # Kiểm tra quyền
    if section.course.lecturer_id != current_user.id:
        return "Từ chối truy cập", 403

    try:
        db.session.delete(section)
        db.session.commit()
        flash("Đã xóa chương thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi: {str(e)}", "danger")

    return redirect(url_for('manage_course', course_id=course_id))


@app.route('/lecturer/lesson/<int:lesson_id>/delete', methods=['POST'])
@login_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.section.course_id

    if lesson.section.course.lecturer_id != current_user.id:
        return "Từ chối truy cập", 403

    db.session.delete(lesson)
    db.session.commit()
    flash("Đã xóa bài học!", "success")
    return redirect(url_for('manage_course', course_id=course_id))


@app.route('/lecturer/lesson/<int:lesson_id>/edit', methods=['POST'])
@login_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    # Kiểm tra quyền chủ sở hữu khóa học
    if lesson.section.course.lecturer_id != current_user.id:
        return "Từ chối truy cập", 403

    # Cập nhật thông tin chữ
    lesson.title = request.form.get('title')
    lesson.content = request.form.get('content')

    # Xử lý nếu giảng viên tải lên video mới
    video_file = request.files.get('video')
    if video_file and video_file.filename != '':
        # Sử dụng hàm upload đã viết trong utils
        video_url = utils.upload_to_cloudinary(video_file, folder="e_course/lessons", resource_type="video")
        lesson.video = video_url

    try:
        db.session.commit()
        flash("Cập nhật bài học thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi: {str(e)}", "danger")

    return redirect(url_for('manage_course', course_id=lesson.section.course_id))


@app.route('/lecturer/section/<int:section_id>/edit', methods=['POST'])
@login_required
def edit_section(section_id):
    section = Section.query.get_or_404(section_id)

    if section.course.lecturer_id != current_user.id:
        return "Từ chối truy cập", 403

    new_name = request.form.get('name')
    if new_name:
        section.title = new_name
        db.session.commit()
        flash("Đã đổi tên chương!", "success")

    return redirect(url_for('manage_course', course_id=section.course_id))

@app.route('/lecturer/course/<int:course_id>/submit', methods=['POST'])
@login_required
def submit_course(course_id):
    course = Course.query.get_or_404(course_id)

    # 1. Kiểm tra quyền sở hữu
    if course.lecturer_id != current_user.id:
        flash("Bạn không có quyền thực hiện thao tác này.", "danger")
        return redirect(url_for('lecturer_dashboard'))

    # 2. Kiểm tra điều kiện nội dung (Phải có ít nhất 1 chương và 1 bài học)
    has_content = False
    if course.sections:
        for section in course.sections:
            if section.lessons:
                has_content = True
                break

    if not has_content:
        flash("Khóa học phải có ít nhất một chương và bài học trước khi gửi duyệt!", "warning")
        return redirect(url_for('manage_course', course_id=course.id))

    # 3. Chuyển trạng thái sang PENDING (Chờ duyệt)
    try:
        course.status = CourseStatus.PENDING # Hoặc 'pending' tùy theo Enum của bạn
        db.session.commit()
        flash(f"Khóa học '{course.title}' đã được gửi duyệt thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi hệ thống: {str(e)}", "danger")

    return redirect(url_for('lecturer_dashboard'))


from sqlalchemy import func
from flask import render_template, current_app


@app.route('/lecturer/statistics')
@login_required
def lecturer_statistics():
    courses = Course.query.filter_by(lecturer_id=current_user.id).all()

    # Dữ liệu cho biểu đồ
    course_labels = [c.title[:15] + '...' if len(c.title) > 15 else c.title for c in courses]
    student_counts = [len(c.enrollments) for c in courses]

    # Tính tổng doanh thu
    total_revenue = sum([len(c.enrollments) * (c.price or 0) for c in courses])

    return render_template('lecturer/statistics.html',
                           courses=courses,
                           course_labels=course_labels,
                           student_counts=student_counts,
                           total_revenue=total_revenue)


# Thêm Route xem chi tiết từng khóa học để nút "Xem chi tiết" hoạt động
# CHỈ GIỮ LẠI MỘT HÀM NÀY CHO ROUTE CHI TIẾT
# --- XÓA TẤT CẢ CÁC ĐOẠN ĐỊNH NGHĨA course_stats CŨ ---

@app.route('/lecturer/statistics/course/<int:course_id>')
@login_required
def course_stats_detail(course_id):
    # Lấy dữ liệu từ utils
    data = utils.get_course_detail_stats(course_id)

    # Kiểm tra quyền chủ sở hữu
    if data['course'].lecturer_id != current_user.id:
        flash("Bạn không có quyền xem thống kê này!", "danger")
        return redirect(url_for('lecturer_statistics'))

    return render_template('lecturer/course_stats_detail.html', **data)

if __name__ == '__main__':
    app.run(debug=True)
