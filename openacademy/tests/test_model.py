import unittest
from openacademy import create_app, db
from openacademy.models import User, Student, Lecturer, UserRole, StudyGoal, StudentLevel, Status


class ModelTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_creation(self):
        u = User(
            first_name="A",
            last_name="Nguyen",
            email="test_user@gmail.com",
            password="hashed_password",
            role=UserRole.USER
        )
        db.session.add(u)
        db.session.commit()

        self.assertEqual(str(u), "Nguyen A")

    def test_polymorphic_student(self):
        s = Student(
            first_name="Hoc",
            last_name="Vien",
            email="student@gmail.com",
            password="1234",
            role=UserRole.STUDENT,
            goal=StudyGoal.UPSKILL,
            level=StudentLevel.BEGINNER
        )
        db.session.add(s)
        db.session.commit()

        queried_user = User.query.filter_by(email="student@gmail.comm").first()
        self.assertIsInstance(queried_user, Student)
        self.assertEqual(queried_user.role, UserRole.STUDENT)


    def test_unique_email_constraint(self):
        u1 = User(first_name="A", last_name="B", email="duplicate@test.com", password="1", role=UserRole.USER)
        db.session.add(u1)
        db.session.commit()

        u2 = User(first_name="C", last_name="D", email="duplicate@test.com", password="2", role=UserRole.USER)
        db.session.add(u2)

        with self.assertRaises(Exception):
            db.session.commit()



if __name__ == '__main__':
    unittest.main()
