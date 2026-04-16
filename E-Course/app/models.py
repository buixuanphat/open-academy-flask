from datetime import datetime, timezone

import enum

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text, Enum as SQLEnum

from sqlalchemy.orm import relationship

from flask_login import UserMixin

from app import db  # Import db từ app/__init__.py





# ==================== ENUMS ====================



class UserRole(enum.Enum):

    STUDENT = "student"

    INSTRUCTOR = "instructor"

    ADMIN = "admin"





class LessonType(enum.Enum):

    VIDEO = "video"

    TEXT = "text"





# ==================== MODELS ====================



class User(db.Model, UserMixin):

    """Yêu cầu 1: Quản lý người dùng"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    username = Column(String(50), unique=True, nullable=False)

    email = Column(String(100), unique=True, nullable=False)

    password_hash = Column(String(255), nullable=False)

    role = Column(SQLEnum(UserRole), default=UserRole.STUDENT)



    # Relationships

    enrollments = relationship("Enrollment", backref="student")

    questions = relationship("Question", backref="author")

    answers = relationship("Answer", backref="author")

    lesson_progress = relationship("LessonProgress", backref="student")





class Category(db.Model):

    """Danh mục khoá học"""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)

    name = Column(String(100), unique=True, nullable=False)

    courses = relationship("Course", backref="category")





class Course(db.Model):

    """Yêu cầu 1 & 4: Thông tin & Quản lý nội dung"""

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)

    title = Column(String(200), nullable=False)

    description = Column(Text)

    image_url = Column(String(255))  # Thêm để lưu ảnh từ Cloudinary

    price = Column(Float, default=0.0)

    category_id = Column(Integer, ForeignKey("categories.id"))

    instructor_id = Column(Integer, ForeignKey("users.id"))



    # Relationships

    sections = relationship("Section", backref="course", cascade="all, delete-orphan")

    enrollments = relationship("Enrollment", backref="course")

    questions = relationship("Question", backref="course")





class Section(db.Model):

    """Yêu cầu 4: Chương học"""

    __tablename__ = "sections"

    id = Column(Integer, primary_key=True)

    course_id = Column(Integer, ForeignKey("courses.id"))

    title = Column(String(200))

    lessons = relationship("Lesson", backref="section", cascade="all, delete-orphan")





class Lesson(db.Model):

    """Yêu cầu 4: Bài học chi tiết"""

    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True)

    section_id = Column(Integer, ForeignKey("sections.id"))

    title = Column(String(200))

    content_url = Column(String(255))

    lesson_type = Column(SQLEnum(LessonType), default=LessonType.VIDEO)

    order = Column(Integer, default=0)





class Enrollment(db.Model):

    """Yêu cầu 2: Đăng ký và Thanh toán"""

    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True)

    student_id = Column(Integer, ForeignKey("users.id"))

    course_id = Column(Integer, ForeignKey("courses.id"))

    payment_status = Column(Boolean, default=False)

    paid_amount = Column(Float, default=0.0)

    enrolled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))





class LessonProgress(db.Model):

    """Yêu cầu 3: Theo dõi tiến độ học tập"""

    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True)

    student_id = Column(Integer, ForeignKey("users.id"))

    lesson_id = Column(Integer, ForeignKey("lessons.id"))

    is_completed = Column(Boolean, default=False)

    completed_at = Column(DateTime)





class Question(db.Model):

    """Yêu cầu 5: Hỏi đáp - Câu hỏi"""

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)

    course_id = Column(Integer, ForeignKey("courses.id"))

    user_id = Column(Integer, ForeignKey("users.id"))

    title = Column(String(255), nullable=False)

    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    answers = relationship("Answer", backref="question", cascade="all, delete-orphan")





class Answer(db.Model):

    """Yêu cầu 5: Hỏi đáp - Câu trả lời"""

    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)

    question_id = Column(Integer, ForeignKey("questions.id"))

    user_id = Column(Integer, ForeignKey("users.id"))

    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


