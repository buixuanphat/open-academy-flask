from openacademy import app, db, utils
from flask import request, redirect, url_for, flash
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from openacademy.models import Category, Course, User, UserRole, Enrollment, Status, Lecturer
from flask_login import logout_user, current_user
from wtforms import TextAreaField
from wtforms.widgets import TextArea


# ==========================================
# 1. PHÂN QUYỀN TRUY CẬP
# ==========================================
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        flash("Bạn cần quyền Admin để vào khu vực này!", "danger")
        return redirect(url_for('auth.login'))  # Thay 'auth.login' bằng route login của bạn


class AuthenticatedView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN


# ==========================================
# 2. TÙY CHỈNH SOẠN THẢO VĂN BẢN (CKEDITOR)
# ==========================================
class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()


# ==========================================
# 3. QUẢN LÝ MODEL (VIEW)
# ==========================================
class CourseModelView(AuthenticatedModelView):
    column_list = ['title', 'price', 'status', 'lecturer', 'created_date']
    column_filters = ['title', 'price', 'status']
    column_searchable_list = ['title', 'description']
    can_view_details = True
    can_export = True
    column_labels = {
        'title': 'Tên khóa học',
        'price': 'Học phí',
        'description': 'Mô tả',
        'status': 'Trạng thái',
        'lecturer': 'Giảng viên'
    }
    # Tích hợp CKEditor cho mô tả khóa học
    extra_js = ['//cdn.ckeditor.com/4.6.0/standard/ckeditor.js']
    form_overrides = {'description': CKTextAreaField}


class UserModelView(AuthenticatedModelView):
    column_list = ['last_name', 'first_name', 'email', 'role', 'active']
    column_exclude_list = ['password']
    column_labels = {'role': 'Quyền', 'active': 'Kích hoạt'}


# ==========================================
# 4. THỐNG KÊ & DASHBOARD
# ==========================================
class StatsView(AuthenticatedView):
    @expose('/')
    def index(self):
        kw = request.args.get('kw')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        # Gọi hàm từ utils
        stats = utils.stats_revenue(kw=kw, from_date=from_date, to_date=to_date)

        # Tính tổng cộng doanh thu để hiển thị ở header
        total_rev = sum(row[2] for row in stats) if stats else 0

        return self.render('admin/stats.html', stats=stats, total_rev=total_rev)


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        # Tận dụng hàm load_categories có sẵn trong utils.py của bạn
        categories = utils.load_categories()

        # Thống kê nhanh cho Dashboard
        total_stats = {
            'users': User.query.count(),
            'courses': Course.query.count(),
            'pending_lecturers': Lecturer.query.filter_by(status=Status.PENDING).count()
        }

        return self.render('admin/index.html', categories=categories, stats=total_stats)


class LogoutView(AuthenticatedView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/login')


# ==========================================
# 5. KHỞI TẠO HỆ THỐNG
# ==========================================
# Sửa lại dòng 114
admin = Admin(app=app, name='EC-ADMIN PANEL', index_view=MyAdminIndexView())

admin.add_view(UserModelView(User, db.session, name='Người dùng'))
admin.add_view(AuthenticatedModelView(Category, db.session, name='Danh mục'))
admin.add_view(CourseModelView(Course, db.session, name='Khóa học'))
admin.add_view(StatsView(name='Báo cáo doanh thu'))
admin.add_view(LogoutView(name='Đăng xuất'))