from flask import render_template, request, redirect, url_for
from app import app, dao, login # Đảm bảo có login_manager nếu dùng Flask-Login

@app.context_processor
def common_data():
    return {
        'categories': dao.get_categories()
    }

@app.route("/")
def index():
    kw = request.args.get('keyword')
    cate_id = request.args.get('category_id')
    courses = dao.get_courses(kw=kw, cate_id=cate_id)
    return render_template('index.html', courses=courses)

@app.route("/course/<int:course_id>")
def course_detail(course_id):
    course = dao.get_course_by_id(course_id)
    if not course:
        return "Không tìm thấy khóa học", 404
    return render_template('courses/detail.html', course=course)

# Route Login giả lập để tránh lỗi BuildError cho đến khi bạn làm trang login thật
@app.route("/login", methods=['GET', 'POST'])
def login_view():
    return "Trang Login - Đang xây dựng"

if __name__ == "__main__":
    # Import admin tại đây để tránh vòng lặp import (Circular Import)
    from app import admin
    app.run(debug=True)