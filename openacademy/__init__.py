from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import cloudinary
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jbcvlgerljblgviyfihuewlfjsdv'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/openacademy?charset=utf8mb4'
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
VNPAY_RETURN_URL = 'https://jettie-unpadlocked-stoutly.ngrok-free.dev/payment_return'