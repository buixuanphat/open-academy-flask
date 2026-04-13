from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import cloudinary
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jbcvlgerljblgviyfihuewlfjsdv'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/openacademydb?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app=app)

cloudinary.config(
    cloud_name='dnbno2tkc',
    api_key='896257422881191',
    api_secret='X6BnafHH4o_-bojDL2gPXzPHQDE'
)

login = LoginManager(app=app)