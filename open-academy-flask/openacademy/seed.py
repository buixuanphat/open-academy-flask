from openacademy import app, db
from openacademy.models import (
    UserRole, StudyGoal, StudentLevel, Status, CourseStatus,
    User, Lecturer, Student, Admin, Category, Course,
    Section, Lesson, Enrollment, Progress
)
import hashlib


def seed_data():
    with app.app_context():
        # 0. Làm sạch dữ liệu
        db.drop_all()
        db.create_all()

        print("--- Đang khởi tạo dữ liệu mẫu chuyên sâu cho Demo ---")

        def hash_pw(password):
            return hashlib.md5(password.encode('utf-8')).hexdigest()

        pass_123 = hash_pw("123456")

        # 1. Tạo Admin
        admin_user = Admin(
            first_name="Admin", last_name="Hệ Thống",
            email="admin@openacademy.com", password=pass_123,
            role=UserRole.ADMIN, avatar="https://ui-avatars.com/api/?name=Admin"
        )
        db.session.add(admin_user)

        # 2. Tạo Giảng viên
        lec = Lecturer(
            first_name="Thanh", last_name="Dương",
            email="giangvien@gmail.com", password=pass_123,
            role=UserRole.LECTURER, bio="Chuyên gia Fullstack Web chuyên nghiệp.",
            status=Status.VERIFIED, avatar="https://i.pravatar.cc/150?u=lec"
        )
        db.session.add(lec)

        # 3. Tạo Học viên mẫu (Mục tiêu: Chuyển ngành, Trình độ: Mới bắt đầu)
        stu = Student(
            first_name="Văn", last_name="Nguyễn",
            email="hocvien@gmail.com", password=pass_123,
            role=UserRole.STUDENT,
            goal=StudyGoal.CAREER_CHANGE,  # QUAN TRỌNG: Để test Recommend
            level=StudentLevel.BEGINNER,  # QUAN TRỌNG: Để test Recommend
            avatar="https://i.pravatar.cc/150?u=stu"
        )
        db.session.add(stu)
        db.session.commit()

        # 4. Tạo Danh mục
        cat_web = Category(name="Lập trình Web")
        cat_data = Category(name="Khoa học dữ liệu")
        db.session.add_all([cat_web, cat_data])
        db.session.commit()

        # ---------------------------------------------------------
        # 5. KHÓA HỌC 1: ĐÃ MUA (Dùng để test logic: Đã mua thì KHÔNG gợi ý lại)
        # ---------------------------------------------------------
        c1 = Course(
            title="Lập trình Flask & SQLAlchemy",
            description="Khóa học này bạn đã mua rồi, nó sẽ không hiện ở mục Gợi ý.",
            price=500000.0, image="https://miro.medium.com/v2/resize:fit:1200/1*on9_9_vshD6_N87m0AnfVw.png",
            category_id=cat_web.id, lecturer_id=lec.id,
            goal=StudyGoal.UPSKILL, level=StudentLevel.BEGINNER, status=CourseStatus.ACTIVE
        )
        db.session.add(c1)
        db.session.commit()

        sec1 = Section(title="Chương 1: Khởi đầu", course_id=c1.id)
        db.session.add(sec1)
        db.session.commit()

        l1 = Lesson(title="Bài 1: Cấu trúc Project", content="Nội dung...",
                    video="https://www.youtube.com/embed/dQw4w9WgXcQ", order_index=1, section_id=sec1.id)
        db.session.add(l1)

        # ---------------------------------------------------------
        # 6. KHÓA HỌC 2: GỢI Ý CHÍNH (Khớp cả Goal & Level)
        # ---------------------------------------------------------
        c2 = Course(
            title="Fullstack Web cho người Chuyển Ngành",
            description="Khóa học này khớp HOÀN HẢO với thông tin của bạn.",
            price=750000.0,
            image="https://www.hostinger.com/tutorials/wp-content/uploads/sites/2/2018/08/how-to-become-a-web-developer.webp",
            category_id=cat_web.id, lecturer_id=lec.id,
            goal=StudyGoal.CAREER_CHANGE, level=StudentLevel.BEGINNER, status=CourseStatus.ACTIVE
        )
        db.session.add(c2)
        db.session.commit()

        sec2 = Section(title="Chương 1: HTML & CSS", course_id=c2.id)
        db.session.add(sec2)
        db.session.commit()
        db.session.add(Lesson(title="Bài 1: Thẻ HTML cơ bản", content="Nội dung...",
                              video="https://www.youtube.com/embed/dQw4w9WgXcQ", order_index=1, section_id=sec2.id))

        # ---------------------------------------------------------
        # 7. KHÓA HỌC 3: GỢI Ý PHỤ (Khớp Goal, nhưng Level cao hơn)
        # ---------------------------------------------------------
        c3 = Course(
            title="Data Analyst cho người muốn đổi nghề",
            description="Mục tiêu Chuyển ngành nhưng ở mức độ Trung cấp.",
            price=1200000.0, image="https://i.ytimg.com/vi/WBy9-B0Xjks/maxresdefault.jpg",
            category_id=cat_data.id, lecturer_id=lec.id,
            goal=StudyGoal.CAREER_CHANGE, level=StudentLevel.INTERMEDIATE, status=CourseStatus.ACTIVE
        )
        db.session.add(c3)
        db.session.commit()

        sec3 = Section(title="Chương 1: Pandas chuyên sâu", course_id=c3.id)
        db.session.add(sec3)
        db.session.commit()
        db.session.add(Lesson(title="Bài 1: Xử lý dữ liệu lớn", content="Nội dung...",
                              video="https://www.youtube.com/embed/dQw4w9WgXcQ", order_index=1, section_id=sec3.id))

        # ---------------------------------------------------------
        # 8. THIẾT LẬP TRẠNG THÁI CHO HỌC VIÊN
        # ---------------------------------------------------------
        # Đăng ký khóa 1
        en = Enrollment(student_id=stu.id, course_id=c1.id, total_payment=500000.0, payment_status=True)
        db.session.add(en)

        # Tiến độ khóa 1
        p1 = Progress(student_id=stu.id, lesson_id=l1.id, percent=100.0)
        db.session.add(p1)

        db.session.commit()
        print("\n--- HOÀN TẤT SEEDING ---")
        print("1. Tài khoản: hocvien@gmail.com / 123456")
        print("2. Logic kiểm tra: Trang chủ sẽ hiện gợi ý Khóa 2 và Khóa 3.")
        print("3. Khóa 1 sẽ bị ẩn vì bạn đã đăng ký mua rồi.")


if __name__ == '__main__':
    seed_data()