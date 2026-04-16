from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import cloudinary

# Khởi tạo DB nhưng chưa gắn với app ngay (để tránh lỗi vòng lặp)
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # --- ĐÂY LÀ ĐOẠN QUAN TRỌNG BẠN ĐANG THIẾU ---
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # Flask-Login lưu ID trong session là chuỗi, cần chuyển sang int để tìm trong DB
        return User.query.get(int(user_id))
    # --------------------------------------------

    cloudinary.config(**app.config['CLOUDINARY_CONFIG'])

    from .routes.auth import auth_bp
    from .routes.student import student_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp)
    from app.routes.instructor import instructor_bp
    app.register_blueprint(instructor_bp)
    return app