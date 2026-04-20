from openacademy.models import *
import hashlib
import hmac
import urllib.parse

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

