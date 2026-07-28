from sqlalchemy import Column,String,Integer,ForeignKey,Boolean,Float
from sqlalchemy.orm import relationship
from database import Base,engine

class User(Base):
    __tablename__ = 'users'
    user_id =Column(Integer, primary_key=True,nullable=False,index =True)
    name =Column(String(200),nullable=False,index=True)
    email =Column(String(200),unique=True,index=True,nullable=False)
    hashed_password = Column(String(255),index=True,nullable=False)
    role = Column(String(50), default="user", nullable=False)
    predictions = relationship("Predictor", back_populates="owner")


class Predictor(Base):
    __tablename__ ='Prediction'

    id = Column(Integer, primary_key=True, index=True)
    age = Column(Float,nullable=False)
    weight= Column(Float,nullable=False)
    height= Column(Float,nullable=False)
    income_lpa= Column(Float,nullable=False)
    smoker= Column(Boolean,nullable=False)
    city= Column(String(100),nullable=False)
    occupation= Column(String(100),nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    predicted_category = Column(String(100), nullable=False)

    owner = relationship("User", back_populates="predictions")