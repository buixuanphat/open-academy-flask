from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from openacademy import db
from openacademy import app

class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

class Category(BaseModel):
    __tablename__ = 'category'
    name = Column(String(30), nullable=False, unique=True)

    def __str__(self):
        return self.name

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
