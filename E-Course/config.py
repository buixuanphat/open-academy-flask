import os
from dotenv import load_dotenv
from urllib.parse import quote

# Nạp file .env
load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Database
    db_user = os.getenv("DB_USER")
    db_password = quote(os.getenv("DB_PASSWORD", ""))
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PAGE_SIZE = int(os.getenv("PAGE_SIZE", 12))

    # Cloudinary
    CLOUDINARY_CONFIG = {
        "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
        "api_key": os.getenv("CLOUDINARY_API_KEY"),
        "api_secret": os.getenv("CLOUDINARY_API_SECRET"),
        "secure": True
    }