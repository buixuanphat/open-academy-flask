from openacademy.models import *
import hashlib
import hmac
import urllib.parse
from sqlalchemy.orm import joinedload

from openacademy.models import Progress

from openacademy.models import Progress, Student, Course, Enrollment, Section, StudentLevel


def add_lecturer(last_name, first_name, email, password, avatar, bio, degrees):
    password= str(hashlib.md5(password.encode('utf-8')).hexdigest())
    new_lecturer = Lecturer(
        last_name=last_name.strip(),
        first_name=first_name.strip(),
        email=email.strip().lower(),
        password=password,
        avatar=avatar,
        role=UserRole.LECTURER,
        active=True,
        bio=bio.strip(),
        status=Status.PENDING
    )

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
        print(f"Lỗi hệ thống: {e}")
        return None


def add_student(last_name, first_name, email, password, avatar, goal, level):
    password= str(hashlib.md5(password.encode('utf-8')).hexdigest())
    new_student = Student(
        last_name=last_name.strip(),
        first_name=first_name.strip(),
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
        print(f"Lỗi hệ thống: {e}")
        return None


def check_login(email, password):
    if email and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

        return User.query.filter(User.email.__eq__(email.strip()),
                                 User.password.__eq__(password)).first()

def get_user_by_id(user_id):
    return User.query.get(user_id)


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


def update_progress(student_id, lesson_id, percent):
    progress = Progress.query.filter_by(student_id=student_id, lesson_id=lesson_id).first()

    if progress:
        if percent > progress.percent:
            progress.percent = percent
    else:
        new_progress = Progress(student_id=student_id, lesson_id=lesson_id, percent=percent)
        db.session.add(new_progress)

    db.session.commit()


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

def level_rank(level):
    order = {
        StudentLevel.BEGINNER: 1,
        StudentLevel.INTERMEDIATE: 2,
        StudentLevel.ADVANCED: 3,
        StudentLevel.EXPERT: 4
    }
    return order.get(level, 0)


def get_first_lesson(course):
    if not course or not course.sections:
        return None

    sorted_sections = sorted(course.sections, key=lambda s: s.id)
    for section in sorted_sections:
        if section.lessons:
            sorted_lessons = sorted(section.lessons, key=lambda l: l.order_index)
            if sorted_lessons:
                return sorted_lessons[0]

    return None


def score_course_for_student(student, course, enrolled_ids, progress_map):
    score = 0
    reasons = []

    if course.goal == student.goal:
        score += 40
        reasons.append("Phù hợp mục tiêu học tập của bạn")

    student_level_rank = level_rank(student.level)
    course_level_rank = level_rank(course.level)
    diff = course_level_rank - student_level_rank

    if diff == 0:
        score += 30
        reasons.append("Đúng với trình độ hiện tại")
    elif diff == 1:
        score += 20
        reasons.append("Phù hợp để học tiếp sau khi nắm nền tảng")
    elif diff > 1:
        score -= 20
        reasons.append("Khóa học này có thể hơi khó ở thời điểm hiện tại")
    else:
        score += 10
        reasons.append("Phù hợp để ôn lại kiến thức nền tảng")

    if course.price == 0:
        score += 5
        reasons.append("Có thể bắt đầu ngay miễn phí")

    if course.id in enrolled_ids:
        percent = progress_map.get(course.id, 0)
        if 0 < percent < 100:
            score += 50
            reasons.append("Bạn đang học dở khóa này")
        elif percent >= 100:
            score -= 100
            reasons.append("Bạn đã hoàn thành khóa này")
        else:
            score += 15
            reasons.append("Bạn đã đăng ký khóa học này")

    return score, reasons


def build_learning_path(student_id):
    student = Student.query.get(student_id)
    if not student:
        return {
            "student": None,
            "continue_courses": [],
            "recommended_courses": [],
            "next_courses": []
        }

    all_courses = Course.query.options(
        joinedload(Course.category),
        joinedload(Course.lecturer),
        joinedload(Course.sections).joinedload(Section.lessons)
    ).all()

    enrollments = Enrollment.query.filter_by(student_id=student_id).all()
    enrolled_ids = {e.course_id for e in enrollments}

    progress_map = {}
    for course in all_courses:
        total_lessons, completed_lessons, progress_percent = calculatecourseprogress(student_id, course.id)
        progress_map[course.id] = progress_percent

    continue_courses = []
    recommended_courses = []
    next_courses = []

    for course in all_courses:
        score, reasons = score_course_for_student(student, course, enrolled_ids, progress_map)
        first_lesson = get_first_lesson(course)
        total_lessons, completed_lessons, progress_percent = calculatecourseprogress(student_id, course.id)

        item = {
            "course": course,
            "score": score,
            "reasons": reasons[:3],
            "progress_percent": progress_percent,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "first_lesson": first_lesson
        }

        if course.id in enrolled_ids and 0 < progress_percent < 100:
            continue_courses.append(item)
        elif course.id not in enrolled_ids:
            if course.goal == student.goal and course.level == student.level:
                recommended_courses.append(item)
            elif level_rank(course.level) == level_rank(student.level) + 1:
                next_courses.append(item)

    continue_courses.sort(key=lambda x: (-x["score"], -x["progress_percent"], x["course"].id))
    recommended_courses.sort(key=lambda x: (-x["score"], x["course"].price, x["course"].id))
    next_courses.sort(key=lambda x: (-x["score"], x["course"].price, x["course"].id))

    return {
        "student": student,
        "continue_courses": continue_courses[:3],
        "recommended_courses": recommended_courses[:6],
        "next_courses": next_courses[:4]
    }