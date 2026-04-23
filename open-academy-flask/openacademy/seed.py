from openacademy import app, db
from openacademy.models import (
    UserRole, StudyGoal, StudentLevel, Status, CourseStatus,
    User, Lecturer, Student, Admin, Category, Course,
    Section, Lesson, Enrollment, Rating, Progress
)
import hashlib

def seed_data():
    with app.app_context():
        # CẢNH BÁO: Xóa sạch dữ liệu để tránh xung đột ID
        db.drop_all()
        db.create_all()

        print("--- Đang khởi tạo dữ liệu mẫu ---")

        # Hàm băm mật khẩu đồng bộ với utils.check_login
        def hash_pw(password):
            return hashlib.md5(password.encode('utf-8')).hexdigest()

        pass_123 = hash_pw("123456")

        # 1. Tạo Admin (Sử dụng đúng Class con Admin)
        admin_user = Admin(
            first_name="Admin",
            last_name="Hệ Thống",
            email="admin@openacademy.com",
            password=pass_123,
            role=UserRole.ADMIN, # Đảm bảo role khớp với identity
            avatar="https://ui-avatars.com/api/?name=Admin"
        )
        db.session.add(admin_user)

        # 2. Tạo Giảng viên
        lec = Lecturer(
            first_name="Thanh",
            last_name="Dương",
            email="giangvien@gmail.com",
            password=pass_123,
            role=UserRole.LECTURER,
            bio="Chuyên gia Fullstack Web với 10 năm kinh nghiệm.",
            status=Status.VERIFIED,
            avatar="https://i.pravatar.cc/150?u=lec"
        )
        db.session.add(lec)

        # 3. Tạo Học viên
        stu = Student(
            first_name="Văn",
            last_name="Nguyễn",
            email="hocvien@gmail.com",
            password=pass_123,
            role=UserRole.STUDENT,
            goal=StudyGoal.CAREER_CHANGE,
            level=StudentLevel.BEGINNER,
            avatar="https://i.pravatar.cc/150?u=stu"
        )
        db.session.add(stu)
        db.session.commit() # Commit để lấy ID cho các bước sau

        # 4. Tạo Danh mục
        cat_web = Category(name="Lập trình Web")
        cat_data = Category(name="Khoa học dữ liệu")
        db.session.add_all([cat_web, cat_data])
        db.session.commit()

        # 5. Tạo Khóa học
        c1 = Course(
            title="Lập trình Flask & SQLAlchemy",
            description="Làm chủ Python Web từ cơ bản đến nâng cao.",
            price=500000.0,
            image="https://miro.medium.com/v2/resize:fit:1200/1*on9_9_vshD6_N87m0AnfVw.png",
            category_id=cat_web.id,
            lecturer_id=lec.id,
            goal=StudyGoal.UPSKILL,
            level=StudentLevel.BEGINNER,
            status=CourseStatus.ACTIVE
        )
        db.session.add(c1)
        db.session.commit()

        # 6. Tạo Chương & Bài học
        sec1 = Section(title="Chương 1: Khởi đầu", course_id=c1.id)
        db.session.add(sec1)
        db.session.commit()

        l1 = Lesson(
            title="Bài 1: Cấu trúc thư mục chuẩn",
            content="Hướng dẫn tổ chức app Flask theo hướng công nghiệp.",
            video="https://www.youtube.com/embed/dQw4w9WgXcQ",
            order_index=1,
            section_id=sec1.id
        )
        l2 = Lesson(
            title="Bài 2: Làm việc với Database",
            content="Cách sử dụng SQLAlchemy hiệu quả.",
            video="https://www.youtube.com/embed/dQw4w9WgXcQ",
            order_index=2,
            section_id=sec1.id
        )
        db.session.add_all([l1, l2])
        db.session.commit()

        # 7. Tạo Đăng ký & Tiến độ
        en = Enrollment(
            student_id=stu.id,
            course_id=c1.id,
            total_payment=500000.0,
            payment_status=True
        )
        db.session.add(en)

        # Tiến độ: Bài 1 học xong (100%), Bài 2 đang học (50%)
        p1 = Progress(student_id=stu.id, lesson_id=l1.id, percent=100.0)
        p2 = Progress(student_id=stu.id, lesson_id=l2.id, percent=50.0)
        db.session.add_all([p1, p2])

        db.session.commit()
        print("--- Hoàn tất Seeding thành công! Tài khoản admin: admin@openacademy.com / 123456 ---")

if __name__ == '__main__':
    seed_data()