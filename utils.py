from passlib.context import CryptContext
from datetime import datetime, timedelta,timezone
from jose import jwt,JWTError
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from model import User
import smtplib
from email.message import EmailMessage
import os

pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password:str)-> str:
    return pwd_context.hash(password)

def verify_hash_password(password:str,hashed_password:str)->bool:
    return pwd_context.verify(password,hashed_password)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))


def create_access_token(data:dict):
  data_copy = data.copy()
  expire_time = datetime.now(timezone.utc) + timedelta(minutes =ACCESS_TOKEN_EXPIRE_MINUTES)
  data_copy.update({'exp':expire_time})
  token = jwt.encode(data_copy,SECRET_KEY,algorithm=ALGORITHM)
  return token

def create_refresh_token (data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt






oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or Token Expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user


def send_email(receipent_email,receiver_name):


   sender_email= os.getenv("sender_email")
   sender_password = os.getenv("sender_password")

   if not sender_email or not sender_password:
        raise HTTPException(status_code= 503, detail= " email or password of sender is ether incoorect or no aviilable in env")

   try:

    #msg name ka object bana liya ai mein ne 
    msg =EmailMessage()

    msg["Subject"] = "Welcome to HealthGuard AI! "
    msg['From'] = sender_email
    msg['To'] = receipent_email

    #ye email mein msg jaye ga

    html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px;">
            <div style="max-width: 500px; margin: auto; background-color: #1e293b; padding: 30px; border-radius: 12px; border: 1px solid #334155;">
                <h2 style="color: #06b6d4; margin-top: 0;">Welcome aboard, {receiver_name}! 👋</h2>
                <p style="color: #cbd5e1; font-size: 15px;">
                    Thank you for creating an account with <b>HealthGuard AI</b>.
                </p>
                <p style="color: #cbd5e1; font-size: 14px;">
                    Your account is now active! You can log in anytime to calculate your Insurance Premium Category.
                </p>
                <div style="margin-top: 25px; padding-top: 15px; border-top: 1px solid #334155; text-align: center;">
                    <p style="color: #64748b; font-size: 12px; margin: 0;">
                        HealthGuard AI • Machine Learning Insurance Prediction System
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP("smtp.gmail.com", 587) as Server:
        Server.starttls()
        Server.login(sender_email,sender_password)
        Server.send_message(msg)

   except Exception:
       print("Email Sending Fail")     


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Check karta hai ke Logged-In User ADMIN hai ya nahi!
    """
    # Agar User ka Role 'admin' nahi hai ──► 403 Forbidden Error Throw Karo!
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Is action ke liye ADMIN rights chahiye!"
        )
        
    return current_user # Valid Admin User Return Kar Diya