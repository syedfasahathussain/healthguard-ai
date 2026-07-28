from fastapi import FastAPI,HTTPException,Depends,BackgroundTasks
from pydantic import BaseModel,Field,field_validator,ConfigDict,computed_field,EmailStr
from typing import Optional
from typing import Literal
import pickle
import pandas as pd
from fastapi.responses import JSONResponse
import model
from database import engine,get_db
from sqlalchemy.orm import Session
import re
from model import User
from utils import get_current_admin_user, hash_password,verify_hash_password,create_access_token,get_current_user,send_email,create_refresh_token 
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt,JWTError
import os
from fastapi import FastAPI, Request # 👈 'Request' import hona zaroori hai!
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


with open('model1.pkl', 'rb') as f:
 model1 = pickle.load(f)

 limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
tier_1_cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune"]
tier_2_cities = [
    "Jaipur", "Chandigarh", "Indore", "Lucknow", "Patna", "Ranchi", "Visakhapatnam", "Coimbatore",
    "Bhopal", "Nagpur", "Vadodara", "Surat", "Rajkot", "Jodhpur", "Raipur", "Amritsar", "Varanasi",
    "Agra", "Dehradun", "Mysore", "Jabalpur", "Guwahati", "Thiruvananthapuram", "Ludhiana", "Nashik",
    "Allahabad", "Udaipur", "Aurangabad", "Hubli", "Belgaum", "Salem", "Vijayawada", "Tiruchirappalli",
    "Bhavnagar", "Gwalior", "Dhanbad", "Bareilly", "Aligarh", "Gaya", "Kozhikode", "Warangal",
    "Kolhapur", "Bilaspur", "Jalandhar", "Noida", "Guntur", "Asansol", "Siliguri"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all frontends (HTML/JS/React)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
class User_input (BaseModel):
    model_config = ConfigDict(extra ='forbid',str_strip_whitespace=True)
    
    age: int = Field(gt=0,lt=150)
    weight: float= Field(gt=0,lt=300,description='Weight should be in kg')
    height: float=Field(gt=0,lt=4,description='Height should be in meters')
    income_lpa: float =Field(gt=0,lt=1000000,description='Value should be in pkr')
    smoker:bool
    city: str ='Mumbai'
    occupation: Literal['retired' ,'freelancer', 'student','government_job' ,'business_owner',
 'unemployed' ,'private_job']

    @field_validator('occupation',mode='before')
    @classmethod
    def normalize_occupation(cls,value):
        if isinstance(value, str):
            return value.lower()
        return value
    @field_validator('city',mode='before')
    @classmethod
    def normalize_city(cls,value):
        return value.title()
    
    @computed_field
    @property
    def bmi(self)->float:
        return self.weight/(self.height**2)
    
    @computed_field
    @property
    def lifestyle_risk(self)->str:
        if self.smoker and self.bmi > 30:
            return "high"
        elif self.smoker or self.bmi > 27:
            return "medium"
        else:
            return "low"
    @computed_field
    @property
    def age_group(self) -> str:
        if self.age < 25: return "young"
        elif self.age < 50: return "adult"      
        elif self.age < 75: return "middle_aged" 
        else: return "Senior"             
    @computed_field
    @property
    def city_tier(self) -> int:
        if self.city in tier_1_cities:
            return 1
        elif self.city in tier_2_cities:
            return 2
        else:
            return 3
    
#p= User_input(age=23,Weight = 60,height =2,income_lpa=400000,smoker=True,city='mumbai', occupation='student')
#p.model_dump()
#p.model_dump_json()
        # return value.lower() ye bhi theek hai but ye or acha option hoga q k agar kisi ne int bhej deya to woh direct chala jaye ga aagye or field mein validation check hojaye gi

class UserCreate(BaseModel):
    name:str 
    email:EmailStr
    password:str
   
    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, value: str):

        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")

        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter.")

        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must contain at least one special character.")

        return value
    
class UserResponse(BaseModel):
    user_id :int
    name:str
    email:str

    model_config = ConfigDict(from_attributes=True)

class LoginValidate(BaseModel):
    email: str
    password: str
# mein Client (Browser) koi JSON Body nahi bhejta to ye hum ye srf is leye baanyi hai hum jb user ko kuch return karen to sirf yehi fields return mein jayen get k leye 
class PredictionResponse(BaseModel):
    id: int
    age: int
    weight: float
    height: float
    income_lpa: float
    smoker: bool
    city: str
    occupation: str
    predicted_category: str
    
    model_config = ConfigDict(from_attributes=True)

class RefreshTokenRequest(BaseModel):
    refresh_token: str
#DATBASE CONNECTION


model.Base.metadata.create_all(bind=engine)
# : ye python mein user hint deta hai ut pydnatic 6 fastapi mein ye proper validation check krta hai : ye cheez 
@app.post("/signup",response_model=UserResponse)
def signup(user:UserCreate,background_tasks: BackgroundTasks,db:Session =Depends(get_db)):
  check_email = db.query(User).filter(User.email==user.email).first()
  if check_email:
    raise HTTPException(status_code= 400, detail ="Email already exist")
  else:
    hashed_password = hash_password(user.password)
    new_user = User(name=user.name,email=user.email,hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    background_tasks.add_task(send_email,new_user.email,new_user.name)

    return new_user

@app.post("/login")
def login(login_user: LoginValidate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_user.email).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    verify_hash = verify_hash_password(login_user.password, user.hashed_password)
    if not verify_hash:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    token = create_access_token(data={'sub': login_user.email})
    refresh_token = create_refresh_token(data={'sub': user.email})

    return {"access_token": token, "refresh_token": refresh_token, "role": user.role,"token_type": "bearer"}
@app.post("/refresh")
def refresh_access_token(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh Token leta hai, verify karta hai, aur NAYA Access Token de deta hai!
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid or Expired Refresh Token! Please login again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. Token Decode Kiya
        payload = jwt.decode(body.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. Check: Kya yeh sach mein Refresh Token hi hai?
        if payload.get("type") != "refresh":
            raise credentials_exception
            
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
    except JWTError: # Expire ya fake token
        raise credentials_exception

    # 3. Check: Kya User MySQL DB mein exist karta hai?
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    # 4. SUCCESS: NAYA ACCESS TOKEN GENERATE KIYA! ⚡
    new_access_token = create_access_token(data={'sub': user.email, 'type': 'access'})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
  
@app.post("/predict")
@limiter.limit("5/minute")

def predict_premium(request: Request,data: User_input, current_user: User = Depends(get_current_user),db:Session=Depends(get_db)):
    print(data.model_dump())
    input_df = pd.DataFrame([{
        'bmi': data.bmi,
        'age_group': data.age_group,
        'lifestyle_risk': data.lifestyle_risk,
        'city_tier': data.city_tier,
        'income_lpa': data.income_lpa,
        'occupation': data.occupation
    }])

    prediction = model1.predict(input_df)[0]

    new_prediction = model.Predictor(
        age=data.age,
        weight=data.weight,
        height=data.height,
        income_lpa=data.income_lpa,
        smoker=data.smoker,
        city=data.city,
        occupation=data.occupation,
        predicted_category=str(prediction),
        user_id=current_user.user_id         
    )
    
    db.add(new_prediction)
    db.commit()
    db.refresh(new_prediction)
    return JSONResponse(status_code=200, content={'predicted_category': prediction})

@app.get("/my-history", response_model=list[PredictionResponse])
def get_my_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  
):
    # Sahi Foreign Key Filtering & Ordering
    history_records = db.query(model.Predictor).filter(
        model.Predictor.user_id == current_user.user_id
    ).order_by(model.Predictor.id.desc()).all()
    
    return history_records

@app.get("/admin/all-predictions")
def get_all_predictions_admin(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user) 
):
    
    # Query MySQL DB for ALL predictions across ALL users
    all_predictions = db.query(model.Predictor).all()
    
    return {
        "admin_email": admin_user.email,
        "total_system_predictions": len(all_predictions),
        "all_records": all_predictions
    }
