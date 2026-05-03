from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import cloudinary
from flask_login import LoginManager
import os
from dotenv import load_dotenv


load_dotenv()

db = SQLAlchemy()
login = LoginManager()


def create_app(config_name='development'):
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'jbcvlgerljblgviyfihuewlfjsdv'

    # chọn DB theo môi trường
    if config_name == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

        if os.getenv('USE_SSL') == 'True':
            ca_path = os.path.join(os.path.dirname(__file__), 'isrgrootx1.pem')
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                "connect_args": {"ssl": {"ca": ca_path}}
            }

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    db.init_app(app)
    login.init_app(app)

    from openacademy.admin import admin
    admin.init_app(app)


    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )


    app.config['VNPAY_TMN_CODE'] = os.getenv('VNPAY_TMN_CODE')
    app.config['VNPAY_HASH_SECRET'] = os.getenv('VNPAY_HASH_SECRET')
    app.config['VNPAY_RETURN_URL'] = os.getenv('VNPAY_RETURN_URL')
    app.config['VNPAY_PAYMENT_URL'] = os.getenv('VNPAY_PAYMENT_URL')

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')

    return app
