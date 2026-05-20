import hashlib
import unittest
from unittest.mock import patch, MagicMock
from flask import url_for, session
from openacademy import create_app, db
from openacademy.models import User, Student, Lecturer, UserRole, Course, CourseStatus, Category, Section, Lesson, \
    StudyGoal
import openacademy.utils as utils


class ControllerTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        # Tạo dữ liệu mẫu: Danh mục
        self.cat = Category(name="Lập trình")
        db.session.add(self.cat)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # --- TEST 1: ĐĂNG KÝ HỌC VIÊN ---
    def test_student_register_post(self):
        response = self.client.post('/student-register', data={
            'first_name': 'An',
            'last_name': 'Nguyen',
            'email': 'an@gmail.com',
            'password': '123',
            'confirm_password': '123',
            'goal': 'UPSKILL',
            'level': 'BEGINNER'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        student = Student.query.filter_by(email='an@gmail.com').first()
        self.assertIsNotNone(student)
        self.assertEqual(student.first_name, 'An')

    # --- TEST 2: QUYỀN TRUY CẬP ---
    def test_lecturer_dashboard_access(self):
        # Đảm bảo người dùng chưa đăng nhập không thể vào Dashboard giảng viên
        response = self.client.get('/lecturer/dashboard')
        # Sẽ redirect về trang login do @login_required
        self.assertEqual(response.status_code, 302)

    # --- TEST 3: CẬP NHẬT TIẾN ĐỘ API ---
    def test_update_progress_api(self):
        # 1. Tạo giảng viên và khóa học mẫu làm gốc
        lecturer = Lecturer(first_name="G", last_name="V", email="gv2@test.com", password="123", role=UserRole.LECTURER, bio="Expert")
        db.session.add(lecturer)
        db.session.commit()

        course = Course(title="Course Test", description="Desc", price=0, category_id=self.cat.id,
                        lecturer_id=lecturer.id, image="image", goal=StudyGoal.UPSKILL, level="BEGINNER")
        db.session.add(course)
        db.session.commit()

        # 2. Tạo Chương (Section) và Bài học (Lesson) có ID = 1
        section = Section(title="Chương 1", course_id=course.id)
        db.session.add(section)
        db.session.commit()

        lesson = Lesson(title="Bài 1", section_id=section.id, content="content", order_index=0)
        db.session.add(lesson)
        db.session.commit()

        # 3. Tạo student
        s = Student(first_name="S",
                    last_name="T",
                    email="s@t.com",
                    password=str(hashlib.md5("1".encode('utf-8')).hexdigest()),
                    role=UserRole.STUDENT,
                    goal="UPSKILL",
                    level="BEGINNER")
        db.session.add(s)
        db.session.commit()

        with self.client:
            self.client.post('/login', data={'email': 's@t.com', 'password': '1'})

            # Gửi request JSON với lesson_id thực tế vừa tạo
            response = self.client.post('/update-progress',
                                        json={
                                            'student_id': s.id,
                                            'lesson_id': lesson.id,
                                            # Dùng trực tiếp lesson.id vừa tạo thay vì gán cứng số 1
                                            'percent': 85.5,
                                            'is_completed': True
                                        }
                                        )

            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['status'], 'success')

    # --- TEST 4: ĐĂNG KÝ BẰNG GOOGLE ---
    def test_student_register_google_session(self):
        # Kiểm tra việc đăng ký học viên khi đã có dữ liệu từ Google trong session
        with self.client.session_transaction() as sess:
            sess['google_user'] = {
                'email': 'google@test.com',
                'first_name': 'Google',
                'last_name': 'User',
                'avatar': 'http://image.com'
            }

        # Truy cập với tham số method=google
        response = self.client.post('/student-register?method=google', data={
            'goal': 'UPSKILL',
            'level': 'BEGINNER'
            # Không cần email/password vì lấy từ session
        }, follow_redirects=True)

        user = User.query.filter_by(email='google@test.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'Google')


if __name__ == '__main__':
    unittest.main()