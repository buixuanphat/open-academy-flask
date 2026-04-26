from openacademy.models import *
from openacademy import db
import hashlib
import hmac
import urllib.parse
import uuid
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_, func, desc
from flask_login import current_user
import cloudinary.uploader


# ==================== USER MANAGEMENT ====================

def add_lecturer(last_name, first_name, email, password, avatar, bio, degrees):
    if password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    else:
        # Nếu đăng ký qua Google, tạo một mật khẩu ngẫu nhiên
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
    return None


def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


# ==================== DATA LOADING ====================

def load_categories():
    return Category.query.order_by(Category.name.asc()).all()


def load_lecturers():
    return Lecturer.query.filter(Lecturer.active == True).all()


def load_courses(kw=None, category_id=None, lecturer_id=None, goal=None, level=None):
    query = Course.query.filter(Course.status == CourseStatus.ACTIVE)

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


# ==================== PROGRESS TRACKING ====================

def load_progress(student_id, lesson_id):
    progress = Progress.query.filter_by(student_id=student_id, lesson_id=lesson_id).first()
    return progress.percent if progress else 0


def update_progress(student_id, lesson_id, percent, is_completed):
    progress = Progress.query.filter_by(student_id=student_id, lesson_id=lesson_id).first()

    if not progress:
        progress = Progress(student_id=student_id, lesson_id=lesson_id, percent=percent, is_completed=is_completed)
        db.session.add(progress)
    else:
        progress.percent = max(progress.percent, percent)
        if not progress.is_completed:
            progress.is_completed = is_completed

    db.session.commit()

    course_finished = False
    if is_completed:
        current_lesson = Lesson.query.get(lesson_id)
        course_id = current_lesson.section.course_id

        all_lesson_ids = db.session.query(Lesson.id).join(Section).filter(Section.course_id == course_id).all()
        all_lesson_ids = [l[0] for l in all_lesson_ids]

        completed_count = Progress.query.filter(
            Progress.student_id == student_id,
            Progress.lesson_id.in_(all_lesson_ids),
            Progress.is_completed == True
        ).count()

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

    progress_percentage = (completed_count / total_lessons * 100) if total_lessons > 0 else 0
    return total_lessons, completed_count, round(progress_percentage, 2)


# ==================== PAYMENT (VNPAY) ====================

class vnpay:
    def __init__(self):
        self.request_data = {}
        self.response_data = {}

    def get_payment_url(self, vnpay_payment_url, secret_key):
        input_data = sorted(self.request_data.items())
        query_string = "&".join(
            [f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(str(v))}" for k, v in input_data])
        hash_value = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha512).hexdigest()
        return f"{vnpay_payment_url}?{query_string}&vnp_SecureHash={hash_value}"

    def validate_response(self, secret_key):
        vnp_secure_hash = self.response_data.get('vnp_SecureHash')
        # Loại bỏ hash để kiểm tra dữ liệu gốc
        data = {k: v for k, v in self.response_data.items() if k not in ['vnp_SecureHash', 'vnp_SecureHashType']}
        input_data = sorted(data.items())
        query_string = "&".join(
            [f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(str(v))}" for k, v in input_data])
        hash_value = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha512).hexdigest()
        return vnp_secure_hash == hash_value


def create_enrollment(student_id, course_id, total_payment):
    existing_enroll = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    if not existing_enroll:
        new_enrollment = Enrollment(
            student_id=student_id, course_id=course_id,
            total_payment=total_payment, payment_status=True
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


# ==================== MEDIA & UPLOAD ====================

def upload_to_cloudinary(file, folder="e_course", resource_type="image"):
    if file and file.filename != '':
        upload_result = cloudinary.uploader.upload(
            file, folder=folder, resource_type=resource_type,
            public_id=f"{resource_type}_{int(datetime.now().timestamp())}"
        )
        return upload_result.get('secure_url')
    return None


# ==================== LECTURER DASHBOARD ====================

def get_courses_by_lecturer(kw=None, status_filter=None, page=1):
    query = Course.query.filter_by(lecturer_id=current_user.id)
    if kw:
        query = query.filter(Course.title.contains(kw))
    if status_filter:
        query = query.filter(Course.status == status_filter)
    return query.order_by(Course.created_date.desc()).paginate(page=page, per_page=5)


def get_lecturer_stats():
    total_courses = Course.query.filter_by(lecturer_id=current_user.id).count()
    active_courses = Course.query.filter_by(lecturer_id=current_user.id, status=CourseStatus.ACTIVE).count()
    total_students = db.session.query(Enrollment).join(Course).filter(Course.lecturer_id == current_user.id).count()
    return {
        'total_courses': total_courses,
        'active_courses': active_courses,
        'total_students': total_students
    }


def add_new_course(data, image_file):
    goal_val = data.get('goal')
    level_val = data.get('level')
    goal_enum = next((g for g in StudyGoal if g.value == goal_val), StudyGoal.UPSKILL)
    level_enum = next((l for l in StudentLevel if l.value == level_val), StudentLevel.BEGINNER)

    image_url = upload_to_cloudinary(image_file, folder="e_course/thumbnails") or ""

    new_course = Course(
        title=data.get('title'),
        description=data.get('description'),
        price=float(data.get('price', 0)),
        category_id=int(data.get('category_id')),
        lecturer_id=current_user.id,
        goal=goal_enum,
        level=level_enum,
        image=image_url
    )
    try:
        db.session.add(new_course)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def get_course_detail_stats(course_id):
    course = Course.query.get_or_404(course_id)
    total_students = len(course.enrollments)
    section_stats = []

    for section in course.sections:
        lessons_detail = []
        total_completed_in_section = 0
        for lesson in section.lessons:
            completed_count = Progress.query.filter_by(lesson_id=lesson.id).filter(Progress.percent >= 90).count()
            total_completed_in_section += completed_count
            lesson_rate = (completed_count / total_students * 100) if total_students > 0 else 0
            lessons_detail.append(
                {'title': lesson.title, 'completed_count': completed_count, 'rate': round(lesson_rate, 1)})

        total_lessons = len(section.lessons)
        section_rate = (total_completed_in_section / (total_lessons * total_students) * 100) if (
                    total_students > 0 and total_lessons > 0) else 0
        section_stats.append({'title': section.title, 'rate': round(section_rate, 1), 'lessons': lessons_detail})

    return {'course': course, 'section_stats': section_stats, 'total_students': total_students}


def add_section_to_course(course_id, title):
    new_section = Section(title=title, course_id=course_id)
    db.session.add(new_section)
    db.session.commit()


def add_lesson_to_section(data, video_file):
    section_id = data.get('section_id')
    current_max_order = db.session.query(func.max(Lesson.order_index)).filter_by(section_id=section_id).scalar() or 0
    video_url = upload_to_cloudinary(video_file, folder="e_course/lessons", resource_type="video")
    new_lesson = Lesson(
        title=data.get('title'), content=data.get('content'),
        video=video_url, section_id=section_id,
        order_index=current_max_order + 1
    )
    db.session.add(new_lesson)
    db.session.commit()


# ==================== ADVANCED LOGIC ====================

def stats_revenue(kw=None, from_date=None, to_date=None):
    query = db.session.query(Course.id, Course.title, func.sum(Enrollment.total_payment), func.count(Enrollment.id)) \
        .join(Enrollment, Enrollment.course_id == Course.id) \
        .filter(Enrollment.payment_status == True)
    if kw:
        query = query.filter(Course.title.contains(kw))
    if from_date:
        query = query.filter(Enrollment.created_date >= from_date)
    if to_date:
        query = query.filter(Enrollment.created_date <= to_date)
    return query.group_by(Course.id).all()


def add_comment(content, lesson_id, user_id, image=None, parent_id=None, is_lecturer=False):
    c = Comment(content=content, lesson_id=lesson_id, user_id=user_id, image=image, parent_id=parent_id, is_lecturer=is_lecturer)
    db.session.add(c)
    db.session.commit()
    return c


def get_recommended_courses(user_id, limit=4):
    student = Student.query.get(user_id)
    if not student: return []

    enrolled_ids = [e.course_id for e in student.enrollments]
    recommended = Course.query.filter(
        Course.status == CourseStatus.ACTIVE,
        Course.id.notin_(enrolled_ids)
    ).filter(
        or_(
            and_(Course.goal == student.goal, Course.level == student.level),
            Course.goal == student.goal
        )
    ).limit(limit).all()
    return recommended


def get_lecturer_comments(lecturer_id):
    return db.session.query(Comment)\
        .join(Lesson, Comment.lesson_id == Lesson.id)\
        .join(Section, Lesson.section_id == Section.id)\
        .join(Course, Section.course_id == Course.id)\
        .filter(Course.lecturer_id == lecturer_id)\
        .order_by(desc(Comment.created_date))\
        .all()