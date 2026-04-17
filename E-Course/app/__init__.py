from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login.init_app(app)


    # Đăng ký Blueprints
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.student import bp as student_bp
    app.register_blueprint(student_bp, url_prefix='/student')

    from app.routes.lecturer import lecturer_bp
    app.register_blueprint(lecturer_bp, url_prefix='/lecturer')

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