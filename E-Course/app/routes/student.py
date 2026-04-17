from flask import Blueprint, render_template, request
from app.models import Course, Category

bp = Blueprint('student', __name__)


@bp.route('/')
def index():
    # Lấy từ khóa tìm kiếm nếu có
    q = request.args.get('q')
    cate_id = request.args.get('category_id')

    query = Course.query

    if q:
        query = query.filter(Course.title.contains(q))
    if cate_id:
        query = query.filter(Course.category_id == cate_id)

    courses = query.all()
    categories = Category.query.all()

    return render_template('student/course_list.html',
                           courses=courses,
                           categories=categories)