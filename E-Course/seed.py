from app import create_app, db
from app.models import (
    UserRole, StudyGoal, StudentLevel, Status, CourseStatus,
    Category, Course, Section, Lesson, Lecturer, Student, User
)
from werkzeug.security import generate_password_hash

app = create_app()

def seed_data():
    with app.app_context():
        # 1. Xóa dữ liệu cũ (Cẩn thận: Lệnh này sẽ xóa sạch DB hiện tại)
        db.drop_all()
        db.create_all()

        print("--- Đang khởi tạo dữ liệu mẫu ---")

        # 2. Tạo Categories
        categories = [
            Category(name="Lập trình Web"),
            Category(name="Thiết kế đồ họa"),
            Category(name="Kinh doanh & Khởi nghiệp"),
            Category(name="Ngoại ngữ")
        ]
        db.session.add_all(categories)
        db.session.commit()

        # 3. Tạo tài khoản mẫu
        # Admin
        admin = User(
            first_name="Admin",
            last_name="System",
            email="admin@gmail.com",
            password=generate_password_hash("123456"),
            role=UserRole.ADMIN
        )

        # Lecturer (Giảng viên)
        lecturer = Lecturer(
            first_name="Văn A",
            last_name="Nguyễn",
            email="giangvien@gmail.com",
            password=generate_password_hash("123456"),
            role=UserRole.LECTURER,
            bio="Chuyên gia với 10 năm kinh nghiệm trong ngành lập trình Fullstack.",
            status=Status.VERIFIED
        )

        # Student (Học viên)
        student = Student(
            first_name="Thanh",
            last_name="Trần",
            email="hocvien@gmail.com",
            password=generate_password_hash("123456"),
            role=UserRole.STUDENT,
            goal=StudyGoal.CAREER_CHANGE,
            level=StudentLevel.BEGINNER
        )

        db.session.add_all([admin, lecturer, student])
        db.session.commit()

        # 4. Tạo Khóa học mẫu (Requirement 4)
        course = Course(
            title="Lập trình Python từ con số 0",
            description="Khóa học dành cho người mới bắt đầu, nắm vững kiến thức nền tảng Python.",
            price=500000.0,
            status= CourseStatus.DRAFT,
            image="python_course.jpg",
            category_id=categories[0].id,
            lecturer_id=lecturer.id,
            goal=StudyGoal.UPSKILL,
            level=StudentLevel.BEGINNER
        )
        db.session.add(course)
        db.session.commit()

        # 5. Tạo Section và Lesson
        section1 = Section(title="Chương 1: Giới thiệu", course_id=course.id)
        db.session.add(section1)
        db.session.commit()

        lesson1 = Lesson(
            title="Cài đặt môi trường",
            content="Hướng dẫn cài đặt Python và VS Code...",
            video="intro_python.mp4",
            order_index=1,
            section_id=section1.id
        )
        lesson2 = Lesson(
            title="Biến và Kiểu dữ liệu",
            content="Cách khai báo biến trong Python...",
            video="variables_python.mp4",
            order_index=2,
            section_id=section1.id
        )
        db.session.add_all([lesson1, lesson2])
        db.session.commit()

        print("--- Đã tạo dữ liệu mẫu thành công! ---")
        print(f"Tài khoản Admin: admin@gmail.com / 123456")
        print(f"Tài khoản Giảng viên: giangvien@gmail.com / 123456")
        print(f"Tài khoản Học viên: hocvien@gmail.com / 123456")

if __name__ == "__main__":
    seed_data()