from flask import Blueprint, render_template
from app.models import Course

student_bp = Blueprint('student', __name__)

# app/routes/student.py

@student_bp.route('/')
def course_list(): # Tên hàm này phải khớp với url_for('student.course_list')
    courses = Course.query.all()
    return render_template('student/course_list.html', courses=courses)