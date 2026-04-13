from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Double
from sqlalchemy.sql.sqltypes import Enum
from sqlalchemy.orm import relationship
from openacademy import db
from openacademy import app
from enum import Enum as UserEnum
from flask_login import UserMixin

class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

class Category(BaseModel):
    __tablename__ = 'category'
    name = Column(String(50), nullable=False, unique=True)
    courses = relationship("Course", backref="category", lazy=True)

    def __str__(self):
        return self.name

class UserRole(UserEnum):
    USER = 0
    ADMIN = 1
    LECTURER = 2
    STUDENT = 3

class StudyGoal(UserEnum):
    UPSKILL = "Nâng cao kỹ năng hiện tại"
    CAREER_CHANGE = "Chuyển đổi nghề nghiệp"
    CERTIFICATION = "Lấy chứng chỉ/Bằng cấp"
    RESEARCH = "Nghiên cứu chuyên sâu"
    HOBBY = "Học vì đam mê/Sở thích"

class StudentLevel(UserEnum):
    BEGINNER = "Người mới bắt đầu (Chưa biết gì)"
    INTERMEDIATE = "Trung cấp (Đã có nền tảng)"
    ADVANCED = "Cao cấp (Thành thạo)"
    EXPERT = "Chuyên gia"

class Status(UserEnum):
    PENDING = 1,
    VERIFIED = 2,
    REJECTED = 3,

class User(BaseModel, UserMixin):
    __tablename__ = 'user'
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(200), nullable=False)
    avatar = Column(String(200), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_date = Column(DateTime, nullable=False, default=datetime.now)
    role = Column(Enum(UserRole), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': UserRole.USER,
        'polymorphic_on': role
    }

    def __str__(self):
        return self.last_name + ' ' + self.first_name

class Lecturer(User):
    __tablename__ = 'lecturer'
    id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    bio = Column(String(200), nullable=False)
    status = Column(Enum(Status), nullable=False, default=Status.PENDING)
    degrees = relationship("Degree", backref="lecturer", lazy='joined')
    courses = relationship("Course", backref="lecturer", lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': UserRole.LECTURER,
    }

class Degree(BaseModel):
    __tablename__ = 'degree'
    name = Column(String(50), nullable=False)
    url = Column(String(200), nullable=False)
    lecturer_id = Column(Integer, ForeignKey('lecturer.id'), nullable=False)

class Student(User):
    __tablename__ = 'student'
    id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    goal = Column(Enum(StudyGoal), nullable=False)
    level = Column(Enum(StudentLevel), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': UserRole.STUDENT,
    }

class Course(BaseModel):
    __tablename__ = 'course'
    title = Column(String(100), nullable=False)
    description = Column(String(200), nullable=False)
    price = Column(Double, nullable=False)
    image = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    lecturer_id = Column(Integer, ForeignKey('lecturer.id'), nullable=False)
    goal = Column(Enum(StudyGoal), nullable=False)
    level = Column(Enum(StudentLevel), nullable=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()


