from app import app, db
from app.models import (User, UserRole, Category, Course, CourseStatus,
                        DifficultyLevel, Section, Lesson, LessonType)


def seed_data():
    with app.app_context():
        # 1. Xóa dữ liệu cũ (Tùy chọn - Cẩn thận khi dùng)
        # db.drop_all()
        # db.create_all()

        # 2. Tạo User Admin & Instructor
        admin = User(
            username="admin",
            email="admin@lms.com",
            full_name="System Administrator",
            role=UserRole.ADMIN
        )
        admin.set_password("123456")

        instructor = User(
            username="giangvien1",
            email="gv1@lms.com",
            full_name="Nguyễn Văn Giảng",
            role=UserRole.INSTRUCTOR,
            bio="Chuyên gia lập trình Python với 10 năm kinh nghiệm."
        )
        instructor.set_password("123456")

        db.session.add_all([admin, instructor])
        db.session.commit()  # Commit để lấy ID cho các bước sau

        # 3. Tạo Categories
        c1 = Category(name="Lập trình Web", slug="lap-trinh-web", description="Các khóa học về HTML, CSS, JS, Flask...")
        c2 = Category(name="Khoa học dữ liệu", slug="data-science", description="Python, Machine Learning, AI...")
        c3 = Category(name="Kỹ năng mềm", slug="soft-skills")

        db.session.add_all([c1, c2, c3])
        db.session.commit()

        # 4. Tạo Khóa học (Courses)
        course1 = Course(
            title="Lập trình Python Web với Flask",
            slug="flask-web-development",
            short_description="Học cách xây dựng hệ thống LMS tích hợp AI.",
            description="Khóa học chuyên sâu về Flask và SQLAlchemy cho người mới bắt đầu.",
            price=500000,
            difficulty=DifficultyLevel.BEGINNER,
            status=CourseStatus.PUBLISHED,
            instructor_id=instructor.id,
            category_id=c1.id,
            requirements=["Căn bản Python", "Biết sử dụng máy tính"],
            objectives=["Xây dựng Web hoàn chỉnh", "Quản lý Database"],
            tags=["Python", "Web", "Flask"]
        )

        course2 = Course(
            title="Nhập môn Trí tuệ nhân tạo (AI)",
            slug="intro-to-ai",
            short_description="Khám phá thế giới AI và Machine Learning.",
            description="Tìm hiểu về Neural Networks, NLP và tương lai của AI.",
            price=1200000,
            discount_price=999000,
            difficulty=DifficultyLevel.INTERMEDIATE,
            status=CourseStatus.PUBLISHED,
            instructor_id=instructor.id,
            category_id=c2.id,
            tags=["AI", "Machine Learning"]
        )

        db.session.add_all([course1, course2])
        db.session.commit()

        # 5. Tạo Chương và Bài học cho khóa 1
        s1 = Section(course_id=course1.id, title="Chương 1: Giới thiệu", order_index=1)
        db.session.add(s1)
        db.session.commit()

        l1 = Lesson(
            section_id=s1.id,
            title="Bài 1: Cài đặt môi trường",
            lesson_type=LessonType.VIDEO,
            content_url="https://youtube.com/embed/example",
            order_index=1,
            is_preview=True
        )
        l2 = Lesson(
            section_id=s1.id,
            title="Bài 2: Cấu trúc thư mục Flask",
            lesson_type=LessonType.TEXT,
            content_text="Đây là nội dung bài học về cấu trúc thư mục...",
            order_index=2
        )

        db.session.add_all([l1, l2])
        db.session.commit()

        print("--- Đã nạp dữ liệu mẫu thành công! ---")


if __name__ == "__main__":
    seed_data()