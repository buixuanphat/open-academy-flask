from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import cloudinary
from flask_login import LoginManager
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jbcvlgerljblgviyfihuewlfjsdv'

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

if os.getenv('USE_SSL') == 'True':
    ca_path = os.path.join(os.path.dirname(__file__), 'isrgrootx1.pem')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "connect_args": {"ssl": {"ca": ca_path}}
    }

db = SQLAlchemy(app=app)

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

login = LoginManager(app=app)

VNPAY_TMN_CODE = os.getenv('VNPAY_TMN_CODE')
VNPAY_HASH_SECRET = os.getenv('VNPAY_HASH_SECRET')
VNPAY_RETURN_URL = os.getenv('VNPAY_RETURN_URL')
VNPAY_PAYMENT_URL = os.getenv('VNPAY_PAYMENT_URL')

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')