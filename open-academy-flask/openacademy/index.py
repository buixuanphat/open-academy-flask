import secrets
import hashlib
import base64
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, session, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests as google_requests
import cloudinary.uploader
from sqlalchemy import func

from openacademy import app, utils, models, login, db, VNPAY_TMN_CODE, VNPAY_RETURN_URL, VNPAY_PAYMENT_URL, \
    VNPAY_HASH_SECRET, GOOGLE_CLIENT_ID, CLIENT_SECRETS_FILE
from openacademy.models import UserRole, Course, Lesson, Category, StudyGoal, StudentLevel, CourseStatus, Section, \
    Enrollment
from openacademy.utils import add_lecturer, add_student, vnpay


# ==========================
# AUTHENTICATION & GOOGLE OAUTH
# ==========================

@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)


@app.route('/login-google')
@app.route('/login-google/<role>')
def login_google(role='STUDENT'):
    local_flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
                "openid"],
        redirect_uri="http://127.0.0.1:5000/callback"
    )

    code_verifier = secrets.token_urlsafe(64)
    session['code_verifier'] = code_verifier

    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').replace('=', '')

    authorization_url, state = local_flow.authorization_url(
        access_type='offline',
        code_challenge=code_challenge,
        code_challenge_method='S256'
    )

    session['oauth_state'] = state
    session['register_role'] = role
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    state = session.get('oauth_state')
    role = session.get('register_role')
    cv = session.get('code_verifier')

    local_flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
                "openid"],
        state=state,
        redirect_uri="http://127.0.0.1:5000/callback"
    )
    local_flow.code_verifier = cv

    try:
        local_flow.fetch_token(authorization_response=request.url)

        credentials = local_flow.credentials
        id_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=google_requests.Request(),
            audience=GOOGLE_CLIENT_ID
        )

        google_user = {
            'email': id_info.get("email"),
            'first_name': id_info.get("given_name"),
            'last_name': id_info.get("family_name"),
            'avatar': id_info.get("picture")
        }

        user = utils.get_user_by_email(email=google_user['email'])
        if user:
            login_user(user)
            session.pop('google_user', None)
            return redirect(url_for('home'))

        session['google_user'] = google_user
        if role == 'lecturer':
            return redirect(url_for('lecturer_register', method='google'))
        else:
            return redirect(url_for('student_register', method='google'))

    except Exception as e:
        print(f"DEBUG CALLBACK ERROR: {str(e)}")
        return f"Lỗi xác thực Google: {str(e)}"


# ==========================
# USER REGISTRATION
# ==========================

@app.route('/lecturer-register', methods=['GET', 'POST'])
def lecturer_register():
    err_msg = ""
    google_data = session.get('google_user') if request.args.get('method') == 'google' else None

    if request.method == 'POST':
        last_name = google_data['last_name'] if google_data else request.form.get('last_name')
        first_name = google_data['first_name'] if google_data else request.form.get('first_name')
        email = google_data['email'] if google_data else request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        bio = request.form.get('bio')

        if not google_data and password != confirm_password:
            err_msg = "Mật khẩu xác nhận không khớp!"
        else:
            try:
                avatar_file = request.files.get('avatar')
                avatar_url = google_data['avatar'] if google_data else None
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
                        degrees_data.append({'name': name_val or file.filename, 'url': res_degree.get('secure_url')})

                new_lecturer = add_lecturer(
                    last_name=last_name, first_name=first_name, email=email,
                    password=password if not google_data else None,
                    avatar=avatar_url, bio=bio, degrees=degrees_data
                )

                if new_lecturer:
                    session.pop('google_user', None)
                    return redirect(url_for('home'))
            except Exception as e:
                err_msg = f"Lỗi hệ thống: {str(e)}"

    return render_template('lecturer_register.html', err_msg=err_msg, google_data=google_data)


@app.route('/student-register', methods=['GET', 'POST'])
def student_register():
    err_msg = ""
    google_data = session.get('google_user') if request.args.get('method') == 'google' else None

    if request.method == 'POST':
        last_name = google_data['last_name'] if google_data else request.form.get('last_name')
        first_name = google_data['first_name'] if google_data else request.form.get('first_name')
        email = google_data['email'] if google_data else request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        goal = request.form.get('goal')
        level = request.form.get('level')

        if not google_data and password != confirm_password:
            err_msg = "Mật khẩu xác nhận không khớp!"
        else:
            try:
                avatar_file = request.files.get('avatar')
                avatar_url = google_data['avatar'] if google_data else None
                if avatar_file:
                    res_avatar = cloudinary.uploader.upload(avatar_file)
                    avatar_url = res_avatar.get('secure_url')

                new_student = add_student(
                    last_name=last_name, first_name=first_name, email=email,
                    password=password if not google_data else None,
                    avatar=avatar_url, goal=goal, level=level
                )

                if new_student:
                    session.pop('google_user', None)
                    return redirect(url_for('home'))
            except Exception as e:
                err_msg = f"Lỗi hệ thống: {str(e)}"

    return render_template('student_register.html', goals=models.StudyGoal, levels=models.StudentLevel, err_msg=err_msg,
                           google_data=google_data)


# ==========================
# GENERAL ROUTES
# ==========================

@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role == UserRole.LECTURER:
            return redirect(url_for('lecturer_dashboard'))
        return redirect(url_for('load_courses'))
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    err_msg = ''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = utils.check_login(email=email, password=password)
        if user:
            login_user(user=user)
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


# ==========================
# COURSE & LEARNING
# ==========================

@app.route('/courses')
def load_courses():
    kw = request.args.get('kw')
    category_id = request.args.get('category_id')
    lecturer_id = request.args.get('lecturer_id')
    goal = request.args.get('goal')
    level = request.args.get('level')

    courses = utils.load_courses(kw, category_id, lecturer_id, goal, level)
    categories = utils.load_categories()
    lecturers = utils.load_lecturers()

    recommended_courses = []
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


@app.route('/my-courses')
@login_required
def load_my_courses():
    kw = request.args.get('kw')
    courses = utils.load_my_courses(current_user.id, kw)
    return render_template('my_courses.html', courses=courses)


@app.route('/courses/<int:course_id>')
def course_detail(course_id):
    course = utils.load_course_details(course_id)
    enrolled_ids = [en.course_id for en in
                    utils.load_enrollments(current_user.id)] if current_user.is_authenticated else []
    return render_template('course_detail.html', course=course, enrolled_ids=enrolled_ids)


@app.route('/learning/<int:course_id>/<int:lesson_id>')
@login_required
def learning(course_id, lesson_id):
    course = utils.load_course_details(course_id)
    current_lesson = Lesson.query.get_or_404(lesson_id)
    return render_template('learning.html', course=course, current_lesson=current_lesson,
                           percent=utils.load_progress(current_user.id, lesson_id),
                           progress=utils.calculate_course_progress(current_user.id, course_id))


@app.route('/update-progress', methods=['POST'])
@login_required
def handle_update_progress():
    data = request.get_json()
    student_id = data.get('student_id')
    lesson_id = data.get('lesson_id')
    percent = data.get('percent')
    is_completed = data.get('is_completed', False)

    course_finished = utils.update_progress(student_id, lesson_id, percent, is_completed)

    return jsonify({
        "status": "success",
        "course_finished": course_finished
    }), 200


@app.route('/enroll-free/<int:course_id>')
@login_required
def enroll_free(course_id):
    course = Course.query.get_or_404(course_id)
    if course.price == 0:
        utils.create_enrollment(current_user.id, course_id, 0)
        if course.sections and course.sections[0].lessons:
            first_lesson_id = course.sections[0].lessons[0].id
            return redirect(url_for('learning', course_id=course.id, lesson_id=first_lesson_id))
    return redirect(url_for('course_detail', course_id=course_id))


# ==========================
# PAYMENT (VNPAY)
# ==========================

@app.route('/payment', methods=['POST'])
@login_required
def payment():
    course_id = request.form.get('course_id')
    amount = int(float(request.form.get('amount'))) * 100
    vnp = vnpay()
    vnp.request_data.update({
        'vnp_Version': '2.1.0', 'vnp_Command': 'pay', 'vnp_TmnCode': VNPAY_TMN_CODE,
        'vnp_Amount': amount, 'vnp_CurrCode': 'VND', 'vnp_TxnRef': f"{course_id}-{datetime.now().strftime('%H%M%S')}",
        'vnp_OrderInfo': request.form.get('order_desc'), 'vnp_OrderType': 'billpayment',
        'vnp_Locale': 'vn', 'vnp_CreateDate': datetime.now().strftime('%Y%m%d%H%M%S'),
        'vnp_IpAddr': request.remote_addr, 'vnp_ReturnUrl': VNPAY_RETURN_URL
    })
    return redirect(vnp.get_payment_url(VNPAY_PAYMENT_URL, VNPAY_HASH_SECRET))


@app.route('/payment_return')
@login_required
def payment_return():
    vnp = vnpay()
    vnp.response_data = request.args.to_dict()
    if vnp.validate_response(VNPAY_HASH_SECRET) and vnp.response_data['vnp_ResponseCode'] == '00':
        course_id = int(vnp.response_data['vnp_TxnRef'].split('-')[0])
        if not Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first():
            db.session.add(Enrollment(student_id=current_user.id, course_id=course_id,
                                      total_payment=float(vnp.response_data['vnp_Amount']) / 100, payment_status=True))
            db.session.commit()
            return "Đăng ký thành công!"
        return "Bạn đã đăng ký khóa học này rồi."
    return "Thanh toán thất bại."


# ==========================
# LECTURER DASHBOARD & MANAGEMENT
# ==========================

@app.route('/lecturer/dashboard')
@login_required
def lecturer_dashboard():
    if current_user.role != UserRole.LECTURER: return redirect(url_for('home'))
    pagination = utils.get_courses_by_lecturer(request.args.get('kw', ''), request.args.get('status', ''),
                                               request.args.get('page', 1, type=int))
    return render_template('lecturer/dashboard.html', pagination=pagination, **utils.get_lecturer_stats(),
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
            db.session.rollback()
            flash(f"Lỗi: {str(e)}", "danger")
    return render_template('lecturer/create_course.html', categories=Category.query.all(), goals=StudyGoal,
                           levels=StudentLevel)

# --- HÀM XÓA KHÓA HỌC (FIX LỖI 500) ---
@app.route('/lecturer/course/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.lecturer_id != current_user.id: abort(403)
    try:
        db.session.delete(course)
        db.session.commit()
        flash("Đã xóa khóa học thành công!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi: {str(e)}", "danger")
    return redirect(url_for('lecturer_dashboard'))


@app.route('/lecturer/course/<int:course_id>/manage')
@login_required
def manage_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.lecturer_id != current_user.id: abort(403)
    return render_template('lecturer/manage_course.html', course=course,
                           sections=Section.query.filter_by(course_id=course_id).all())


@app.route('/lecturer/course/<int:course_id>/section/add', methods=['POST'])
@login_required
def add_section(course_id):
    if request.form.get('name'):
        utils.add_section_to_course(course_id, request.form.get('name'))
    return redirect(url_for('manage_course', course_id=course_id))


@app.route('/lecturer/course/lesson/add', methods=['POST'])
@login_required
def add_lesson():
    course_id = request.form.get('course_id')
    try:
        utils.add_lesson_to_section(request.form, request.files.get('video'))
    except Exception as e:
        flash(f"Lỗi: {str(e)}", "danger")
    return redirect(url_for('manage_course', course_id=course_id))


@app.route('/lecturer/section/<int:section_id>/delete', methods=['POST'])
@login_required
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)
    course_id = section.course_id
    if section.course.lecturer_id != current_user.id: return "Từ chối truy cập", 403
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
    if lesson.section.course.lecturer_id != current_user.id: return "Từ chối truy cập", 403
    db.session.delete(lesson)
    db.session.commit()
    flash("Đã xóa bài học!", "success")
    return redirect(url_for('manage_course', course_id=course_id))


@app.route('/lecturer/lesson/<int:lesson_id>/edit', methods=['POST'])
@login_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.section.course.lecturer_id != current_user.id: return "Từ chối truy cập", 403
    lesson.title = request.form.get('title')
    lesson.content = request.form.get('content')
    video_file = request.files.get('video')
    if video_file:
        video_url = utils.upload_to_cloudinary(video_file, folder="e_course/lessons", resource_type="video")
        if video_url: lesson.video = video_url
    db.session.commit()
    flash("Cập nhật thành công!", "success")
    return redirect(url_for('manage_course', course_id=lesson.section.course_id))


@app.route('/lecturer/section/<int:section_id>/edit', methods=['POST'])
@login_required
def edit_section(section_id):
    section = Section.query.get_or_404(section_id)
    if section.course.lecturer_id != current_user.id: return "Từ chối truy cập", 403
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
    if course.lecturer_id != current_user.id:
        flash("Bạn không có quyền thực hiện thao tác này.", "danger")
        return redirect(url_for('lecturer_dashboard'))
    has_content = any(section.lessons for section in course.sections)
    if not has_content:
        flash("Khóa học phải có ít nhất một chương và bài học trước khi gửi duyệt!", "warning")
        return redirect(url_for('manage_course', course_id=course.id))
    try:
        course.status = CourseStatus.PENDING
        db.session.commit()
        flash(f"Khóa học '{course.title}' đã được gửi duyệt!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi hệ thống: {str(e)}", "danger")
    return redirect(url_for('lecturer_dashboard'))


# ==========================
# STATISTICS & API
# ==========================

@app.route('/lecturer/statistics')
@login_required
def lecturer_statistics():
    courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    labels = [c.title[:15] + '...' if len(c.title) > 15 else c.title for c in courses]
    counts = [len(c.enrollments) for c in courses]
    return render_template('lecturer/statistics.html', courses=courses, course_labels=labels,
                           student_counts=counts,
                           total_revenue=sum([len(c.enrollments) * (c.price or 0) for c in courses]))


@app.route('/lecturer/statistics/course/<int:course_id>')
@login_required
def course_stats_detail(course_id):
    data = utils.get_course_detail_stats(course_id)
    if data['course'].lecturer_id != current_user.id: abort(403)
    return render_template('lecturer/course_stats_detail.html', **data)


@app.route('/api/lessons/<int:lesson_id>/comments', methods=['POST'])
@login_required
def add_comment_api(lesson_id):
    content = request.form.get('content')
    parent_id = request.form.get('parent_id')
    file = request.files.get('image')
    image_url = utils.upload_to_cloudinary(file) if file else None

    if content or image_url:
        try:
            c = utils.add_comment(content=content, lesson_id=lesson_id, user_id=current_user.id,
                                  image=image_url, parent_id=parent_id)
            return jsonify({
                "id": c.id, "content": c.content, "image": c.image,
                "created_date": c.created_date.strftime('%H:%M %d/%m'),
                "user": {"full_name": f"{current_user.last_name} {current_user.first_name}", "avatar": current_user.avatar}
            }), 201
        except Exception as e:
            return jsonify({"error": "Lỗi lưu bình luận"}), 500
    return jsonify({"error": "Nội dung không được trống"}), 400


if __name__ == '__main__':
    app.run(debug=True)