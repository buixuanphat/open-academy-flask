from openacademy import db
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Enum, Text,
                        Double)
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from flask_login import UserMixin

class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now)

# ENUM
class UserRole(PyEnum):
    USER = "Người dùng"
    ADMIN = "Quản trị viên"
    LECTURER = "Giảng viên"
    STUDENT = "Học viên"

class StudyGoal(PyEnum):
    UPSKILL = "Nâng cao kỹ năng"
    CAREER_CHANGE = "Chuyển đổi nghề nghiệp"
    CERTIFICATION = "Lấy chứng chỉ"
    RESEARCH = "Nghiên cứu"
    HOBBY = "Sở thích"

class StudentLevel(PyEnum):
    BEGINNER = "Người mới bắt đầu"
    INTERMEDIATE = "Trung cấp"
    ADVANCED = "Nâng cao"
    EXPERT = "Chuyên gia"

class Status(PyEnum):
    PENDING = "Đang chờ"
    VERIFIED = "Đã xác thực"
    REJECTED = "Đã từ chối"

class CourseStatus(PyEnum):
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"


class User(BaseModel, UserMixin):
    __tablename__ = 'user'
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    avatar = Column(String(200))
    active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), nullable=False)

    comments = relationship("Comment", backref="user", lazy=True)
    ratings = relationship("Rating", backref="user", lazy=True)

    __mapper_args__ = {
        'polymorphic_identity': UserRole.USER,
        'polymorphic_on': role
    }

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

class Admin(User):
    __tablename__ = 'admin'
    id = Column(Integer, ForeignKey('user.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': UserRole.ADMIN, # Giữ nguyên như này nếu Enum hoạt động tốt
    }

class Lecturer(User):
    __tablename__ = 'lecturer'
    id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    bio = Column(Text, nullable=False)
    status = Column(Enum(Status), default=Status.PENDING)

    degrees = relationship("Degree", backref="lecturer", lazy=True, cascade="all, delete-orphan")
    courses = relationship("Course", backref="lecturer", lazy=True)

    __mapper_args__ = {'polymorphic_identity': UserRole.LECTURER}


class Student(User):
    __tablename__ = 'student'
    id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    goal = Column(Enum(StudyGoal), nullable=False)
    level = Column(Enum(StudentLevel), nullable=False)

    enrollments = relationship("Enrollment", backref="student", lazy=True, cascade="all, delete-orphan")
    progresses = relationship("Progress", backref="student", lazy=True, cascade="all, delete-orphan")

    __mapper_args__ = {'polymorphic_identity': UserRole.STUDENT}


class Category(BaseModel):
    __tablename__ = 'category'
    name = Column(String(50), unique=True, nullable=False)
    courses = relationship("Course", backref="category", lazy=True)


class Course(BaseModel):
    __tablename__ = 'course'
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    status = Column(Enum(CourseStatus), default=CourseStatus.DRAFT)
    image = Column(String(200), nullable=False)

    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    lecturer_id = Column(Integer, ForeignKey('lecturer.id'), nullable=False)

    goal = Column(Enum(StudyGoal), nullable=False)
    level = Column(Enum(StudentLevel), nullable=False)

    sections = relationship("Section", backref="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", backref="course", lazy=True)
    ratings = relationship("Rating", backref="course", lazy=True, cascade="all, delete-orphan")


class Section(BaseModel):
    __tablename__ = 'section'
    title = Column(String(100), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    lessons = relationship("Lesson", backref="section", cascade="all, delete-orphan")


class Lesson(BaseModel):
    __tablename__ = 'lesson'
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    video = Column(String(200))
    order_index = Column(Integer, nullable=False)
    section_id = Column(Integer, ForeignKey('section.id'), nullable=False)

    comments = relationship("Comment", backref="lesson", lazy=True, cascade="all, delete-orphan")
    progresses = relationship("Progress", backref="lesson", lazy=True)


class Enrollment(BaseModel):
    __tablename__ = 'enrollment'
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    total_payment = Column(Float, nullable=False)
    payment_status = Column(Boolean, default=False)
    finish = Column(Boolean, default=False)

    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='unique_student_course'),)


class Progress(BaseModel):
    __tablename__ = 'progress'
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False)
    lesson_id = Column(Integer, ForeignKey('lesson.id'), nullable=False)
    is_completed = Column(Boolean, default=False)
    percent = Column(Double, nullable=False)

    __table_args__ = (UniqueConstraint('student_id', 'lesson_id', name='unique_student_lesson'),)


class Comment(BaseModel):
    __tablename__ = 'comment'
    content = Column(String(500), nullable=False)
    image = Column(String(200), nullable=False)
    is_lecturer = Column(Boolean, default=False)
    lesson_id = Column(Integer, ForeignKey('lesson.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('comment.id'))

    replies = relationship(
        "Comment",
        backref=db.backref('parent', remote_side='Comment.id'),
        lazy=True,
        cascade="all, delete-orphan"
    )


class Rating(BaseModel):
    __tablename__ = 'rating'
    score = Column(Integer, nullable=False)
    review = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    __table_args__ = (UniqueConstraint('course_id', 'user_id', name='unique_course_user_rating'),)


class Degree(BaseModel):
    __tablename__ = 'degree'
    name = Column(String(50), nullable=False)
    url = Column(String(200), nullable=False)
    lecturer_id = Column(Integer, ForeignKey('lecturer.id'), nullable=False)
