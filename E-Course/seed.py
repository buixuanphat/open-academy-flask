from app import create_app, db
from app.models import User, UserRole, Category, Course
from werkzeug.security import generate_password_hash

app = create_app()

def seed_data():
    with app.app_context():
        # 1. Xóa và tạo mới toàn bộ bảng
        db.drop_all()
        db.create_all()

        # 2. Tạo Category mẫu
        cat1 = Category(name="Lập trình Web")
        cat2 = Category(name="Khoa học dữ liệu")
        db.session.add_all([cat1, cat2])

        # 3. Tạo User mẫu (Giảng viên)
        instructor = User(
            username="giangvien1",
            email="gv1@example.com",
            password_hash=generate_password_hash("123456"),
            role=UserRole.INSTRUCTOR
        )
        db.session.add(instructor)
        db.session.commit() # Commit để lấy ID của instructor và category

        # 4. Tạo Khóa học mẫu
        course1 = Course(
            title="Lập trình Flask cơ bản",
            description="Khóa học hướng dẫn xây dựng website với Python và Flask",
            price=500000.0,
            category_id=cat1.id,
            instructor_id=instructor.id
        )
        db.session.add(course1)
        db.session.commit()

        print("Đã tạo dữ liệu mẫu thành công!")

if __name__ == "__main__":
    seed_data()