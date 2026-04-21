from flask import Flask,redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'

class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.value == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login.init_app(app)

    admin = Admin(app, name='E-Course Admin')

    # Đăng ký Blueprints
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.student import bp as student_bp
    app.register_blueprint(student_bp, url_prefix='/student')

    from app.routes.lecturer import lecturer_bp
    app.register_blueprint(lecturer_bp, url_prefix='/lecturer')

    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    @app.template_filter('format_number')
    def format_number(value):
        if value is None:
            return "0"
        return "{:,}".format(value).replace(",", ".")

    return app

@login.user_loader
def load_user(user_id):
    # PHẢI import cả Student và Lecturer ở đây
    # để SQLAlchemy biết cách chuyển đổi (cast) từ User sang subclass
    from app.models import User, Student, Lecturer
    return User.query.get(int(user_id))