from datetime import datetime

from flask import render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required

from openacademy import app, utils, models, login, VNPAY_TMN_CODE, VNPAY_RETURN_URL, VNPAY_PAYMENT_URL, \
    VNPAY_HASH_SECRET
import cloudinary.uploader

from openacademy.models import UserRole, Course, Lesson
from openacademy.utils import add_lecturer, add_student, vnpay

from openacademy.models import Enrollment, db
from flask_login import current_user



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
    if request.method.__eq__('POST'):
        email = request.form.get('email')
        password = request.form.get('password')

        user = utils.check_login(email=email, password=password)
        if user:
            login_user(user=user)
            if user.role.__eq__(UserRole.STUDENT):
                return redirect(url_for('load_courses'))
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
    kw = request.args.get('kw')
    category_id = request.args.get('category_id')
    lecturer_id = request.args.get('lecturer_id')
    goal = request.args.get('goal')
    level = request.args.get('level')

    courses = utils.load_courses(kw, category_id, lecturer_id, goal, level)

    categories = utils.load_categories()
    lecturers = utils.load_lecturers()

    return render_template('courses.html',
                           courses=courses,
                           categories=categories,
                           lecturers=lecturers,
                           goals=models.StudyGoal,
                           levels=models.StudentLevel)


@app.route('/my-courses', methods=['GET'])
def load_my_courses():
    kw = request.args.get('kw')

    courses = utils.load_my_courses(current_user.id, kw)

    return render_template('my_courses.html', courses=courses)

@app.route('/learning-path', methods=['GET'])
@login_required
def learning_path():
    if current_user.role != UserRole.STUDENT:
        return redirect(url_for('home'))

    roadmap = utils.build_learning_path(current_user.id)
    return render_template('learning_path.html', roadmap=roadmap)


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



if __name__ == '__main__':
    app.run(debug=True)
