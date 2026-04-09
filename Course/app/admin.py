from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, request
from app.models import (User, Category, Course, Section, Lesson, Question,
                        Answer, Enrollment, Payment, UserRole, db)
import json
from app import dao


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        stats = dao.get_admin_stats()
        return self.render('admin/index.html', stats=stats)

    def is_accessible(self):
        # Mở khóa để bạn vào được /admin (Sau này đổi thành logic bên dưới)
        return True
        # return current_user.is_authenticated and current_user.role == UserRole.ADMIN


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return True  # Mở khóa tạm thời để test các bảng
        # return current_user.is_authenticated and current_user.role == UserRole.ADMIN


class CourseModelView(AuthenticatedModelView):
    column_display_pk = True
    column_list = ('id', 'title', 'category', 'price', 'status')

    # Xử lý lưu dữ liệu JSON từ form
    def on_model_change(self, form, model, is_created):
        if not model.slug:
            model.slug = model.title.lower().replace(" ", "-")

        for field in ['requirements', 'objectives', 'tags']:
            val = getattr(model, field)
            if isinstance(val, str):
                try:
                    setattr(model, field, json.loads(val))
                except:
                    setattr(model, field, [])


# Khởi tạo Admin
from app import app

admin = Admin(app, name='LMS ADMIN', template_mode='bootstrap4', index_view=MyAdminIndexView())

admin.add_view(AuthenticatedModelView(User, db.session, category="Hệ thống"))
admin.add_view(AuthenticatedModelView(Category, db.session, category="Nội dung"))
admin.add_view(CourseModelView(Course, db.session, category="Nội dung"))
admin.add_view(AuthenticatedModelView(Lesson, db.session, category="Nội dung"))
admin.add_view(AuthenticatedModelView(Enrollment, db.session, category="Kinh doanh"))