from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SQLEnum, Boolean, Date, DateTime, Text, JSON
from app import db, app
from enum import Enum as RoleEnum
import hashlib
from flask_login import UserMixin
from datetime import datetime, timezone, date


# ==================== ENUMS ====================

class UserRole(RoleEnum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


class CourseStatus(RoleEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class EnrollmentStatus(RoleEnum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(RoleEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(RoleEnum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    MOMO = "momo"
    VNPAY = "vnpay"
    FREE = "free"


class DifficultyLevel(RoleEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LessonType(RoleEnum):
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"


class QuestionStatus(RoleEnum):
    OPEN = "open"
    ANSWERED = "answered"
    CLOSED = "closed"


class NotificationType(RoleEnum):
    ENROLLMENT = "enrollment"
    PAYMENT = "payment"
    PROGRESS = "progress"
    QA = "qa"
    RECOMMENDATION = "recommendation"
    SYSTEM = "system"


# ==================== YÊU CẦU 1: USER & COURSE INFO ====================

class User(db.Model, UserMixin):
    """Người dùng hệ thống (học viên, giảng viên, admin)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    avatar_url = Column(String(255))
    bio = Column(Text)
    role = Column(SQLEnum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    enrollments = relationship("Enrollment", back_populates="student", foreign_keys="Enrollment.student_id")
    courses_taught = relationship("Course", back_populates="instructor", foreign_keys="Course.instructor_id")
    payments = relationship("Payment", back_populates="user")
    learning_profile = relationship("LearningProfile", back_populates="user", uselist=False)
    questions = relationship("Question", back_populates="author", foreign_keys="Question.author_id")
    answers = relationship("Answer", back_populates="author", foreign_keys="Answer.author_id")
    notifications = relationship("Notification", back_populates="user")
    reviews = relationship("CourseReview", back_populates="student")

    def set_password(self, password: str):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"


class Category(db.Model):
    """Danh mục khoá học"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(120), nullable=False, unique=True)
    description = Column(Text)
    icon_url = Column(String(255))
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Self-referential relationship (subcategory)
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    courses = relationship("Course", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


class Course(db.Model):
    """Khoá học"""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(220), nullable=False, unique=True)
    description = Column(Text)
    short_description = Column(String(300))
    thumbnail_url = Column(String(255))
    preview_video_url = Column(String(255))
    price = Column(Float, default=0.0)
    discount_price = Column(Float, nullable=True)
    difficulty = Column(SQLEnum(DifficultyLevel), default=DifficultyLevel.BEGINNER)
    status = Column(SQLEnum(CourseStatus), default=CourseStatus.DRAFT)
    language = Column(String(50), default="Vietnamese")
    duration_hours = Column(Float, default=0.0)   # Tổng thời lượng (giờ)
    requirements = Column(JSON)                    # Yêu cầu đầu vào (list)
    objectives = Column(JSON)                      # Mục tiêu khoá học (list)
    tags = Column(JSON)                            # Tags tìm kiếm (list)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime, nullable=True)

    # Relationships
    instructor = relationship("User", back_populates="courses_taught", foreign_keys=[instructor_id])
    category = relationship("Category", back_populates="courses")
    sections = relationship("Section", back_populates="course", cascade="all, delete-orphan",
                            order_by="Section.order_index")
    enrollments = relationship("Enrollment", back_populates="course")
    reviews = relationship("CourseReview", back_populates="course")
    questions = relationship("Question", back_populates="course")

    @property
    def average_rating(self) -> float:
        if not self.reviews:
            return 0.0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    @property
    def total_students(self) -> int:
        return len([e for e in self.enrollments if e.status == EnrollmentStatus.ACTIVE])

    @property
    def effective_price(self) -> float:
        return self.discount_price if self.discount_price is not None else self.price

    def __repr__(self):
        return f"<Course {self.title}>"


class CourseReview(db.Model):
    """Đánh giá khoá học"""
    __tablename__ = "course_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Float, nullable=False)         # 1.0 – 5.0
    comment = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    course = relationship("Course", back_populates="reviews")
    student = relationship("User", back_populates="reviews")

    def __repr__(self):
        return f"<Review course={self.course_id} rating={self.rating}>"


# ==================== YÊU CẦU 2: ĐĂNG KÝ & THANH TOÁN ====================

class Enrollment(db.Model):
    """Đăng ký khoá học"""
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    status = Column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.PENDING)
    enrolled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    expiry_date = Column(Date, nullable=True)       # Ngày hết hạn truy cập

    student = relationship("User", back_populates="enrollments", foreign_keys=[student_id])
    course = relationship("Course", back_populates="enrollments")
    payment = relationship("Payment", back_populates="enrollment", uselist=False)
    progress_records = relationship("LessonProgress", back_populates="enrollment",
                                    cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Enrollment student={self.student_id} course={self.course_id}>"


class Payment(db.Model):
    """Thanh toán khoá học"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="VND")
    method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.CREDIT_CARD)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String(100), unique=True, nullable=True)  # Mã giao dịch cổng TT
    gateway_response = Column(JSON, nullable=True)                    # Raw response từ cổng TT
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="payments")
    enrollment = relationship("Enrollment", back_populates="payment")

    def __repr__(self):
        return f"<Payment {self.transaction_id} {self.status.value}>"


class Coupon(db.Model):
    """Mã giảm giá"""
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    discount_percent = Column(Float, nullable=True)   # % giảm
    discount_amount = Column(Float, nullable=True)    # Số tiền giảm cố định
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)  # NULL = áp dụng mọi khoá
    is_active = Column(Boolean, default=True)

    course = relationship("Course")

    def __repr__(self):
        return f"<Coupon {self.code}>"


# ==================== YÊU CẦU 3: THEO DÕI TIẾN ĐỘ HỌC TẬP ====================

class Section(db.Model):
    """Chương / phần của khoá học"""
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, default=0)

    course = relationship("Course", back_populates="sections")
    lessons = relationship("Lesson", back_populates="section", cascade="all, delete-orphan",
                           order_by="Lesson.order_index")

    def __repr__(self):
        return f"<Section {self.title}>"


class Lesson(db.Model):
    """Bài học trong khoá học"""
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    title = Column(String(200), nullable=False)
    lesson_type = Column(SQLEnum(LessonType), default=LessonType.VIDEO)
    content_url = Column(String(255), nullable=True)   # URL video hoặc tài liệu
    content_text = Column(Text, nullable=True)         # Nội dung text/markdown
    duration_minutes = Column(Integer, default=0)
    order_index = Column(Integer, default=0)
    is_preview = Column(Boolean, default=False)        # Bài học xem trước miễn phí

    section = relationship("Section", back_populates="lessons")
    progress_records = relationship("LessonProgress", back_populates="lesson")
    quiz = relationship("Quiz", back_populates="lesson", uselist=False)
    questions = relationship("Question", back_populates="lesson")

    def __repr__(self):
        return f"<Lesson {self.title} ({self.lesson_type.value})>"


class LessonProgress(db.Model):
    """Tiến độ học từng bài"""
    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    is_completed = Column(Boolean, default=False)
    watch_duration_seconds = Column(Integer, default=0)   # Thời gian đã xem (giây)
    last_position_seconds = Column(Integer, default=0)    # Vị trí video cuối cùng
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    enrollment = relationship("Enrollment", back_populates="progress_records")
    lesson = relationship("Lesson", back_populates="progress_records")

    def __repr__(self):
        return f"<LessonProgress enrollment={self.enrollment_id} lesson={self.lesson_id}>"


class Quiz(db.Model):
    """Quiz / bài kiểm tra trong bài học"""
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    title = Column(String(200), nullable=False)
    pass_score = Column(Float, default=70.0)   # Điểm qua (%)
    time_limit_minutes = Column(Integer, nullable=True)

    lesson = relationship("Lesson", back_populates="quiz")
    quiz_questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz")

    def __repr__(self):
        return f"<Quiz {self.title}>"


class QuizQuestion(db.Model):
    """Câu hỏi trong quiz"""
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)         # [{"id": "A", "text": "..."}, ...]
    correct_answer = Column(String(10), nullable=False)
    explanation = Column(Text)
    order_index = Column(Integer, default=0)

    quiz = relationship("Quiz", back_populates="quiz_questions")

    def __repr__(self):
        return f"<QuizQuestion quiz={self.quiz_id}>"


class QuizAttempt(db.Model):
    """Lần làm quiz của học viên"""
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Float, default=0.0)
    answers = Column(JSON)            # {"question_id": "selected_answer", ...}
    is_passed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    submitted_at = Column(DateTime, nullable=True)

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("User")

    def __repr__(self):
        return f"<QuizAttempt quiz={self.quiz_id} student={self.student_id} score={self.score}>"


# ==================== YÊU CẦU 4: TẠO & QUẢN LÝ NỘI DUNG KHOÁ HỌC ====================

class CourseResource(db.Model):
    """Tài nguyên đính kèm của khoá học (PDF, ZIP, link...)"""
    __tablename__ = "course_resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    title = Column(String(200), nullable=False)
    file_url = Column(String(255), nullable=False)
    file_type = Column(String(50))     # pdf, zip, link, ...
    file_size_kb = Column(Integer, nullable=True)

    lesson = relationship("Lesson")

    def __repr__(self):
        return f"<CourseResource {self.title}>"


class Announcement(db.Model):
    """Thông báo của giảng viên trong khoá học"""
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    course = relationship("Course")
    instructor = relationship("User")

    def __repr__(self):
        return f"<Announcement {self.title}>"


class Assignment(db.Model):
    """Bài tập / assignment của khoá học"""
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime, nullable=True)
    max_score = Column(Float, default=100.0)

    lesson = relationship("Lesson")
    submissions = relationship("AssignmentSubmission", back_populates="assignment",
                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Assignment {self.title}>"


class AssignmentSubmission(db.Model):
    """Bài nộp của học viên"""
    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_url = Column(String(255), nullable=True)
    content_text = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    graded_at = Column(DateTime, nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User")

    def __repr__(self):
        return f"<AssignmentSubmission assignment={self.assignment_id} student={self.student_id}>"


# ==================== YÊU CẦU 5: HỎI ĐÁP TRONG KHOÁ HỌC ====================

class Question(db.Model):
    """Câu hỏi của học viên trong khoá học"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(SQLEnum(QuestionStatus), default=QuestionStatus.OPEN)
    is_pinned = Column(Boolean, default=False)
    upvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    course = relationship("Course", back_populates="questions")
    lesson = relationship("Lesson", back_populates="questions")
    author = relationship("User", back_populates="questions", foreign_keys=[author_id])
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Question {self.title[:40]}>"


class Answer(db.Model):
    """Câu trả lời cho câu hỏi (từ giảng viên, học viên hoặc AI)"""
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)   # NULL nếu là AI
    body = Column(Text, nullable=False)
    is_accepted = Column(Boolean, default=False)    # Câu trả lời được chấp nhận
    is_ai_generated = Column(Boolean, default=False)
    upvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    question = relationship("Question", back_populates="answers")
    author = relationship("User", back_populates="answers", foreign_keys=[author_id])

    def __repr__(self):
        return f"<Answer question={self.question_id} ai={self.is_ai_generated}>"


# ==================== TÍNH NĂNG AI: GỢI Ý & CÁ NHÂN HOÁ ====================

class LearningProfile(db.Model):
    """Hồ sơ học tập – dùng cho AI gợi ý và cá nhân hoá lộ trình"""
    __tablename__ = "learning_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    career_goals = Column(JSON)             # ["backend developer", "data engineer", ...]
    skill_level = Column(JSON)              # {"python": "intermediate", "sql": "beginner", ...}
    preferred_languages = Column(JSON)      # ["Python", "JavaScript", ...]
    preferred_difficulty = Column(SQLEnum(DifficultyLevel), nullable=True)
    available_hours_per_week = Column(Float, nullable=True)
    learning_style = Column(String(50), nullable=True)  # "visual", "reading", "hands-on"
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="learning_profile")

    def __repr__(self):
        return f"<LearningProfile user={self.user_id}>"


class LearningPath(db.Model):
    """Lộ trình học cá nhân hoá"""
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    goal = Column(String(300))             # Mục tiêu nghề nghiệp cụ thể
    is_ai_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    path_items = relationship("LearningPathItem", back_populates="path",
                              cascade="all, delete-orphan", order_by="LearningPathItem.order_index")

    def __repr__(self):
        return f"<LearningPath {self.title} user={self.user_id}>"


class LearningPathItem(db.Model):
    """Khoá học trong lộ trình học"""
    __tablename__ = "learning_path_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    order_index = Column(Integer, default=0)
    is_required = Column(Boolean, default=True)
    reason = Column(Text)    # Lý do AI gợi ý khoá này

    path = relationship("LearningPath", back_populates="path_items")
    course = relationship("Course")

    def __repr__(self):
        return f"<LearningPathItem path={self.path_id} course={self.course_id}>"


class CourseRecommendation(db.Model):
    """Kết quả gợi ý khoá học từ AI"""
    __tablename__ = "course_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    score = Column(Float, default=0.0)          # Điểm liên quan (0-1)
    reason = Column(Text)                        # Giải thích lý do gợi ý
    source = Column(String(50))                  # "collaborative", "content", "career_goal"
    is_viewed = Column(Boolean, default=False)
    is_enrolled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    course = relationship("Course")

    def __repr__(self):
        return f"<Recommendation user={self.user_id} course={self.course_id} score={self.score}>"


class UserActivityLog(db.Model):
    """Nhật ký hoạt động học tập – dùng làm input cho hệ thống gợi ý"""
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)

    # ĐỔI TÊN Ở ĐÂY: từ metadata -> data_info hoặc extra_data
    data_info = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")

    def __repr__(self):
        return f"<ActivityLog user={self.user_id} type={self.activity_type}>"


# ==================== TIỆN ÍCH ====================

class Notification(db.Model):
    """Thông báo cho người dùng"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    link = Column(String(255), nullable=True)    # Deep link đến trang liên quan
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification user={self.user_id} type={self.type.value}>"


# ==================== TẠO BẢNG ====================

with app.app_context():
    db.create_all()