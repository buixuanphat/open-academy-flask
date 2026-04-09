from app.models import (User, Category, Course, Enrollment, Payment,
                        UserRole, CourseStatus, db)
from sqlalchemy import func


def get_categories():
    return Category.query.all()


def get_courses(kw=None, cate_id=None):
    query = Course.query.filter(Course.status == CourseStatus.PUBLISHED)
    if kw:
        query = query.filter(Course.title.contains(kw))
    if cate_id:
        query = query.filter(Course.category_id == cate_id)
    return query.all()


def get_course_by_id(course_id):
    return Course.query.get(course_id)


def get_admin_stats():
    # Sử dụng scalar() và xử lý None cho doanh thu
    revenue = db.session.query(func.sum(Payment.amount)) \
        .filter(Payment.status == "success").scalar()

    return {
        'total_courses': Course.query.count(),
        'total_students': User.query.filter(User.role == UserRole.STUDENT).count(),
        'total_revenue': revenue or 0,
        'recent_enrollments': Enrollment.query.order_by(Enrollment.enrolled_at.desc()).limit(5).all()
    }