from openacademy.models import *
import hashlib
import hmac
import urllib.parse
from sqlalchemy.orm import joinedload

from openacademy.models import Progress

from flask_login import current_user
from sqlalchemy import func
import cloudinary.uploader

import hashlib
import uuid

def add_lecturer(last_name, first_name, email, password, avatar, bio, degrees):
    if password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    else:
        password = str(hashlib.md5(str(uuid.uuid4()).encode('utf-8')).hexdigest())

    new_lecturer = Lecturer(
        last_name=last_name.strip() if last_name else "",
        first_name=first_name.strip() if first_name else "",
        email=email.strip().lower(),
        password=password,
        avatar=avatar,
        role=UserRole.LECTURER,
        active=True,
        bio=bio.strip() if bio else "",
        status=Status.PENDING
    )

    if degrees:
        for degree in degrees:
            new_degree = Degree(
                name=degree['name'],
                url=degree['url'],
            )
            new_lecturer.degrees.append(new_degree)

    try:
        db.session.add(new_lecturer)
        db.session.commit()
        return new_lecturer
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi hệ thống (add_lecturer): {e}")
        return None


def add_student(last_name, first_name, email, password, avatar, goal, level):
    if password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    else:
        password = str(hashlib.md5(str(uuid.uuid4()).encode('utf-8')).hexdigest())

    new_student = Student(
        last_name=last_name.strip() if last_name else "",
        first_name=first_name.strip() if first_name else "",
        email=email.strip().lower(),
        password=password,
        avatar=avatar,
        role=UserRole.STUDENT,
        active=True,
        goal=goal,
        level=level,
    )

    try:
        db.session.add(new_student)
        db.session.commit()
        return new_student
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi hệ thống (add_student): {e}")
        return None


def check_login(email, password):
    if email and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

        return User.query.filter(User.email.__eq__(email.strip()),
                                 User.password.__eq__(password)).first()

def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def load_categories():
    return Category.query.order_by(Category.name.asc()).all()

def load_lecturers():
    return Lecturer.query.filter(Lecturer.active == True).all()


def load_courses(kw=None, category_id=None, lecturer_id=None, goal=None, level=None):
    query = Course.query

    if kw:
        query = query.filter(Course.title.contains(kw))

    if category_id:
        query = query.filter(Course.category_id == category_id)

    if lecturer_id:
        query = query.filter(Course.lecturer_id == lecturer_id)

    if goal:
        query = query.filter(Course.goal == goal)

    if level:
        query = query.filter(Course.level == level)

    return query.all()


def load_enrollments(student_id):
    return Enrollment.query.filter_by(student_id=student_id).all()


def load_course_details(course_id):
    return Course.query.options(
        joinedload(Course.sections).joinedload(Section.lessons)
    ).get_or_404(course_id)


def load_progress(student_id, lesson_id):
    progress = Progress.query.filter_by(student_id=student_id, lesson_id=lesson_id).first()

    if progress:
        return progress.percent
    return 0


def update_progress(student_id, lesson_id, percent, is_completed):
    # 1. Cập nhật hoặc tạo mới tiến độ bài học
    progress = Progress.query.filter_by(student_id=student_id, lesson_id=lesson_id).first()

    if not progress:
        progress = Progress(student_id=student_id, lesson_id=lesson_id, percent=percent, is_completed=is_completed)
        db.session.add(progress)
    else:
        progress.percent = max(progress.percent, percent)
        # Nếu đã từng hoàn thành thì giữ True, nếu chưa thì cập nhật theo data mới
        if not progress.is_completed:
            progress.is_completed = is_completed

    db.session.commit()

    # 2. Logic kiểm tra hoàn thành khóa học
    course_finished = False
    if is_completed:
        # Lấy lesson hiện tại để tìm ra khóa học (Course)
        current_lesson = Lesson.query.get(lesson_id)
        course_id = current_lesson.section.course_id

        # Lấy danh sách tất cả ID bài học của khóa học này
        all_lesson_ids = db.session.query(Lesson.id).join(Section).filter(Section.course_id == course_id).all()
        all_lesson_ids = [l[0] for l in all_lesson_ids]

        # Đếm số bài học mà sinh viên này đã hoàn thành trong khóa học này
        completed_count = Progress.query.filter(
            Progress.student_id == student_id,
            Progress.lesson_id.in_(all_lesson_ids),
            Progress.is_completed == True
        ).count()

        # Nếu số bài đã học xong == tổng số bài của khóa học
        if completed_count == len(all_lesson_ids):
            enrollment = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
            if enrollment and not enrollment.finish:
                enrollment.finish = True
                course_finished = True
                db.session.commit()

    return course_finished


def calculate_course_progress(student_id, course_id):
    course = Course.query.get(course_id)
    if not course or not course.sections:
        return 0, 0, 0

    total_lessons = 0
    completed_count = 0

    for section in course.sections:
        for lesson in section.lessons:
            total_lessons += 1

            percent = load_progress(student_id, lesson.id)
            if percent >= 90:
                completed_count += 1

    if total_lessons == 0:
        return 0, 0, 0

    progress_percentage = (completed_count / total_lessons) * 100

    return total_lessons, completed_count, round(progress_percentage, 2)


class vnpay:
    request_data = {}
    response_data = {}

    def __init__(self):
        self.request_data = {}
        self.response_data = {}

    def get_payment_url(self, vnpay_payment_url, secret_key):
        input_data = sorted(self.request_data.items())
        query_string = ""
        has_data = False
        seq = 0
        for key, val in input_data:
            if has_data:
                query_string += "&"
            query_string += urllib.parse.quote_plus(key) + "=" + urllib.parse.quote_plus(str(val))
            has_data = True

        hash_value = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha512).hexdigest()
        return vnpay_payment_url + "?" + query_string + "&vnp_SecureHash=" + hash_value

    def validate_response(self, secret_key):
        vnp_secure_hash = self.response_data.get('vnp_SecureHash')
        if 'vnp_SecureHash' in self.response_data:
            self.response_data.pop('vnp_SecureHash')
        if 'vnp_SecureHashType' in self.response_data:
            self.response_data.pop('vnp_SecureHashType')

        input_data = sorted(self.response_data.items())
        has_data = False
        query_string = ""
        for key, val in input_data:
            if has_data:
                query_string += "&"
            query_string += urllib.parse.quote_plus(key) + "=" + urllib.parse.quote_plus(str(val))
            has_data = True

        hash_value = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha512).hexdigest()
        return vnp_secure_hash == hash_value


def create_enrollment(student_id, course_id, total_payment):
    existing_enroll = Enrollment.query.filter_by(
        student_id=student_id,
        course_id=course_id
    ).first()

    if not existing_enroll:
        new_enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            total_payment=total_payment,
            payment_status=True
        )
        db.session.add(new_enrollment)
        db.session.commit()
        return "Chúc mừng! Bạn đã đăng ký khóa học thành công."

    return "Khóa học này bạn đã đăng ký rồi."


def load_my_courses(student_id, kw=None):
    query = db.session.query(Course).join(Enrollment, Enrollment.course_id == Course.id) \
        .filter(Enrollment.student_id == student_id)

    if kw:
        query = query.filter(Course.title.contains(kw))

    courses = query.all()

    for c in courses:
        total, completed, overall_percent = calculate_course_progress(student_id, c.id)

        c.total_lessons = total
        c.completed_lessons = completed
        c.progress_percent = overall_percent

    return courses

# ==================== LOGIC UPLOAD ====================
def upload_to_cloudinary(file, folder="e_course", resource_type="image"):
    if file and file.filename != '':
        upload_result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type=resource_type,
            public_id=f"{resource_type}_{int(datetime.now().timestamp())}"
        )
        return upload_result.get('secure_url')
    return None

# ==================== LOGIC TRUY VẤN (DAO) ====================

def get_courses_by_lecturer(kw=None, status_filter=None, page=1):
    query = Course.query.filter_by(lecturer_id=current_user.id)
    if kw:
        query = query.filter(Course.title.contains(kw))
    if status_filter:
        query = query.filter(Course.status == status_filter)
    return query.order_by(Course.created_date.desc()).paginate(page=page, per_page=5)

def get_lecturer_stats():
    # Thống kê tổng quan cho Dashboard giảng viên
    total_courses = Course.query.filter_by(lecturer_id=current_user.id).count()
    active_courses = Course.query.filter_by(lecturer_id=current_user.id, status=CourseStatus.ACTIVE).count()
    total_students = db.session.query(Enrollment).join(Course).filter(Course.lecturer_id == current_user.id).count()
    return {
        'total_courses': total_courses,
        'active_courses': active_courses,
        'total_students': total_students
    }


def add_new_course(data, image_file):
    title = data.get('title')
    description = data.get('description')
    price = float(data.get('price', 0))
    category_id = int(data.get('category_id'))

    # CHỖ NÀY QUAN TRỌNG: Chuyển chuỗi tiếng Việt thành Enum Object
    # Ta tìm Enum có .value trùng với chuỗi gửi lên từ Form
    goal_val = data.get('goal')
    level_val = data.get('level')

    goal_enum = next((g for g in StudyGoal if g.value == goal_val), StudyGoal.UPSKILL)
    level_enum = next((l for l in StudentLevel if l.value == level_val), StudentLevel.BEGINNER)

    # Upload ảnh lên Cloudinary
    image_url = ""
    if image_file:
        res = cloudinary.uploader.upload(image_file, folder="e_course/thumbnails")
        image_url = res.get('secure_url')

    new_course = Course(
        title=title,
        description=description,
        price=price,
        category_id=category_id,
        lecturer_id=current_user.id,
        goal=goal_enum,  # Truyền đối tượng Enum vào đây
        level=level_enum,  # Truyền đối tượng Enum vào đây
        image=image_url
    )

    try:
        db.session.add(new_course)
        db.session.commit()
    except Exception as e:
        db.session.rollback()  # Giải phóng session để tránh PendingRollbackError
        raise e


def get_course_detail_stats(course_id):
    course = Course.query.get_or_404(course_id)
    total_students = len(course.enrollments)

    section_stats = []

    for section in course.sections:
        lessons_in_section = section.lessons
        lessons_detail = []
        total_completed_in_section = 0

        for lesson in lessons_in_section:
            # Đếm số học viên hoàn thành bài học này
            completed_count = Progress.query.filter_by(lesson_id=lesson.id).filter(Progress.percent >= 90).count()
            total_completed_in_section += completed_count

            # Tính % hoàn thành của riêng bài học này
            lesson_rate = (completed_count / total_students * 100) if total_students > 0 else 0

            lessons_detail.append({
                'title': lesson.title,
                'completed_count': completed_count,
                'rate': round(lesson_rate, 1)
            })

        # Tính % trung bình của cả chương
        total_lessons = len(lessons_in_section)
        if total_students > 0 and total_lessons > 0:
            section_rate = (total_completed_in_section / (total_lessons * total_students)) * 100
        else:
            section_rate = 0

        section_stats.append({
            'title': section.title,
            'rate': round(section_rate, 1),
            'lessons': lessons_detail  # Danh sách bài học chi tiết
        })

    return {
        'course': course,
        'section_stats': section_stats,
        'total_students': total_students
    }

    return {
        'course': course,
        'section_labels': section_labels,
        'section_data': section_completion_rates,  # Bây giờ là % hoàn thành
        'total_students': total_students
    }
def add_section_to_course(course_id, title):
    new_section = Section(title=title, course_id=course_id)
    db.session.add(new_section)
    db.session.commit()


def add_lesson_to_section(data, video_file):
    section_id = data.get('section_id')
    # Tự động tính order_index tiếp theo
    current_max_order = db.session.query(func.max(Lesson.order_index)).filter_by(section_id=section_id).scalar() or 0

    video_url = upload_to_cloudinary(video_file, folder="e_course/lessons", resource_type="video")
    new_lesson = Lesson(
        title=data.get('title'),
        content=data.get('content'),
        video=video_url,
        section_id=section_id,
        order_index=current_max_order + 1  # Tự tăng index
    )
    db.session.add(new_lesson)
    db.session.commit()

def stats_revenue(kw=None, from_date=None, to_date=None):
    # Truy vấn: Tên khóa học, Tổng doanh thu, Số lượng học viên
    query = db.session.query(Course.id, Course.title,
                            func.sum(Enrollment.total_payment),
                            func.count(Enrollment.id)) \
                      .join(Enrollment, Enrollment.course_id == Course.id) \
                      .filter(Enrollment.payment_status == True)

    if kw:
        query = query.filter(Course.title.contains(kw))

    if from_date:
        query = query.filter(Enrollment.created_date >= from_date)

    if to_date:
        query = query.filter(Enrollment.created_date <= to_date)

    return query.group_by(Course.id).all()



def add_comment(content, lesson_id, user_id, image=None, parent_id=None):
    c = Comment(content=content,
                lesson_id=lesson_id,
                user_id=user_id,
                image=image,
                parent_id=parent_id)
    db.session.add(c)
    db.session.commit()
    return c