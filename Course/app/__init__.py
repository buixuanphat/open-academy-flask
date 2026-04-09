from flask import Flask
from urllib.parse import quote
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary
from unidecode import unidecode

app = Flask(__name__)
app.secret_key = "KJGHJG^&*%&*^T&*(IGFG%ERFTGHCFHGFasdasIU"

# Cấu hình Database
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/coursedb?charset=utf8mb4" % quote('aiconcha123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 3

db = SQLAlchemy(app)
login = LoginManager(app)

# --- CẤU HÌNH CLOUDINARY ---
cloudinary.config(
    cloud_name="dd1frsvzk",
    api_key="172266497937733",
    api_secret="W_FvA2NSah3Jlv8cxhubvnw2mVM",
    secure=True
)

# --- JINJA FILTERS ---
@app.template_filter('intcomma')
def intcomma_filter(value):
    if value is None:
        return 0
    return "{:,}".format(value)

@app.template_filter('remove_accents')
def remove_accents_filter(s):
    if s is None:
        return ""
    return unidecode(s)

# --- ĐĂNG KÝ USER LOADER ---
from app.models import User

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- IMPORT ADMIN & ROUTES TẠI ĐÂY ---
# Phải để cuối cùng để tránh lỗi Circular Import
from app import admin
# from app import index # Nếu bạn có file index.py xử lý các route chính