
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import cloudinary
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jbcvlgerljblgviyfihuewlfjsdv'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://4CCvs9sf8gjYoXM.root:iR1UeuaX8zThkwil@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/sys?ssl_ca=/etc/ssl/certs/ca-certificates.crt'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app=app)

cloudinary.config(
    cloud_name='dnbno2tkc',
    api_key='896257422881191',
    api_secret='X6BnafHH4o_-bojDL2gPXzPHQDE'
)

login = LoginManager(app=app)

VNPAY_TMN_CODE = 'Z5IJKQGT'
VNPAY_HASH_SECRET = 'DHI759AV08T7N8188OECPJ1XLUCCUE8E'
VNPAY_PAYMENT_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
VNPAY_RETURN_URL = 'https://open-academy.onrender.com/payment_return'

from . import admin


import os
from google_auth_oauthlib.flow import Flow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secret.json")

GOOGLE_CLIENT_ID = "466909840388-7d6tnnjremfnadn2dk5s91drjcq428n8.apps.googleusercontent.com"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
