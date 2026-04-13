from sqlalchemy.sql.operators import bitwise_or_op

from openacademy import db
from openacademy.models import *
import hashlib

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


def check_login(username, password):
    if username and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

        return User.query.filter(User.username.__eq__(username.strip()),
                                 User.password.__eq__(password)).first()

def get_user_by_id(user_id):
    return User.query.get(user_id)