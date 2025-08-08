from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import bcrypt
import uuid
import stripe
import os
import shutil
from pathlib import Path
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db, User as UserModel, BlogPost as BlogPostModel, Content as ContentModel, init_database
import json

app = FastAPI(title="Linkware Consulting Platform", version="1.0.0")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")

security = HTTPBearer()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleLogin(BaseModel):
    token: str

class User(BaseModel):
    id: str
    email: str
    full_name: str
    company: Optional[str] = None
    membership_type: str = "free"
    created_at: datetime

class BlogPostCreate(BaseModel):
    title: str
    content: str
    category: str
    tags: List[str] = []
    is_premium: bool = False

class BlogPost(BaseModel):
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    is_premium: bool
    author_id: str
    created_at: datetime
    updated_at: datetime

class MembershipUpgrade(BaseModel):
    membership_type: str  # "premium" or "enterprise"

class PaymentIntentCreate(BaseModel):
    membership_type: str
    payment_method_id: Optional[str] = None

class ContentUpdate(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None

class Content(BaseModel):
    id: str
    title: str
    content: str
    image_url: Optional[str] = None
    updated_at: datetime

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return {
            "id": user.id,
            "email": user.email,
            "password": user.password,
            "full_name": user.full_name,
            "company": user.company,
            "membership_type": user.membership_type,
            "created_at": user.created_at
        }
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)), db: Session = Depends(get_db)):
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user is None:
            return None
        return {
            "id": user.id,
            "email": user.email,
            "password": user.password,
            "full_name": user.full_name,
            "company": user.company,
            "membership_type": user.membership_type,
            "created_at": user.created_at
        }
    except jwt.PyJWTError:
        return None

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/auth/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    db_user = UserModel(
        id=user_id,
        email=user_data.email,
        password=hashed_password,
        full_name=user_data.full_name,
        company=user_data.company,
        membership_type="free",
        created_at=datetime.utcnow()
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "full_name": db_user.full_name,
            "company": db_user.company,
            "membership_type": db_user.membership_type,
            "created_at": db_user.created_at
        }
    }

@app.post("/api/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "company": user.company,
            "membership_type": user.membership_type,
            "created_at": user.created_at
        }
    }

@app.post("/api/auth/google")
async def google_login(google_data: GoogleLogin, db: Session = Depends(get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(
            google_data.token, 
            requests.Request(), 
            os.getenv("GOOGLE_CLIENT_ID")
        )
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        
        user = db.query(UserModel).filter(UserModel.email == email).first()
        
        if not user:
            user_id = str(uuid.uuid4())
            user = UserModel(
                id=user_id,
                email=email,
                password="",
                full_name=name,
                company=None,
                membership_type="free",
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        access_token = create_access_token(data={"sub": user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "company": user.company,
                "membership_type": user.membership_type,
                "created_at": user.created_at
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Google authentication failed")

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return User(**{k: v for k, v in current_user.items() if k != "password"})

@app.post("/api/membership/upgrade")
async def upgrade_membership(
    membership_data: MembershipUpgrade,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if membership_data.membership_type not in ["premium", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid membership type")
    
    user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.membership_type = membership_data.membership_type
    db.commit()
    
    return {"message": f"Membership upgraded to {membership_data.membership_type}"}

@app.get("/api/blog/posts")
async def get_blog_posts(
    category: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    query = db.query(BlogPostModel)
    
    if current_user is None or current_user["membership_type"] == "free":
        query = query.filter(BlogPostModel.is_premium == False)
    
    if category:
        query = query.filter(BlogPostModel.category == category)
    
    posts = query.order_by(desc(BlogPostModel.created_at)).all()
    
    result = []
    for post in posts:
        result.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "category": post.category,
            "tags": post.get_tags(),
            "is_premium": post.is_premium,
            "author_id": post.author_id,
            "created_at": post.created_at,
            "updated_at": post.updated_at
        })
    
    return result

@app.get("/api/blog/posts/{post_id}")
async def get_blog_post(post_id: str, current_user: Optional[dict] = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.is_premium and (current_user is None or current_user["membership_type"] == "free"):
        raise HTTPException(status_code=403, detail="Premium membership required")
    
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "tags": post.get_tags(),
        "is_premium": post.is_premium,
        "author_id": post.author_id,
        "created_at": post.created_at,
        "updated_at": post.updated_at
    }

@app.post("/api/blog/posts")
async def create_blog_post(
    post_data: BlogPostCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["membership_type"] == "free":
        raise HTTPException(status_code=403, detail="Premium membership required to create posts")
    
    post_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    blog_post = BlogPostModel(
        id=post_id,
        title=post_data.title,
        content=post_data.content,
        category=post_data.category,
        is_premium=post_data.is_premium,
        author_id=current_user["id"],
        created_at=now,
        updated_at=now
    )
    blog_post.set_tags(post_data.tags)
    
    db.add(blog_post)
    db.commit()
    db.refresh(blog_post)
    
    return {
        "id": blog_post.id,
        "title": blog_post.title,
        "content": blog_post.content,
        "category": blog_post.category,
        "tags": blog_post.get_tags(),
        "is_premium": blog_post.is_premium,
        "author_id": blog_post.author_id,
        "created_at": blog_post.created_at,
        "updated_at": blog_post.updated_at
    }

@app.get("/api/blog/categories")
async def get_blog_categories(db: Session = Depends(get_db)):
    categories = db.query(BlogPostModel.category).distinct().all()
    return [category[0] for category in categories]

@app.get("/api/content/about")
async def get_about_content(db: Session = Depends(get_db)):
    about_content = db.query(ContentModel).filter(ContentModel.id == "about").first()
    if not about_content:
        raise HTTPException(status_code=404, detail="About content not found")
    return {
        "id": about_content.id,
        "title": about_content.title,
        "content": about_content.content,
        "image_url": about_content.image_url,
        "updated_at": about_content.updated_at
    }

@app.post("/api/content/about/upload-image")
async def upload_about_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if current_user["membership_type"] != "enterprise" or current_user["email"] != "admin@linkware.com":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    max_size = 5 * 1024 * 1024
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(status_code=400, detail="File too large")
    
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    unique_filename = f"about_{uuid.uuid4()}.{file_extension}"
    file_path = f"uploads/about/{unique_filename}"
    
    os.makedirs("uploads/about", exist_ok=True)
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
    
    return {"image_url": f"/uploads/about/{unique_filename}"}

@app.put("/api/content/about")
async def update_about_content(
    content_data: ContentUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["membership_type"] != "enterprise" or current_user["email"] != "admin@linkware.com":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    about_content = db.query(ContentModel).filter(ContentModel.id == "about").first()
    if not about_content:
        raise HTTPException(status_code=404, detail="About content not found")
    
    about_content.title = content_data.title
    about_content.content = content_data.content
    about_content.image_url = content_data.image_url
    about_content.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(about_content)
    
    return {
        "id": about_content.id,
        "title": about_content.title,
        "content": about_content.content,
        "image_url": about_content.image_url,
        "updated_at": about_content.updated_at
    }

@app.post("/api/membership/create-payment-intent")
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        prices = {
            "premium": 4900,  # $49.00 in cents
            "enterprise": 19900  # $199.00 in cents
        }
        
        if payment_data.membership_type not in prices:
            raise HTTPException(status_code=400, detail="Invalid membership type")
        
        amount = prices[payment_data.membership_type]
        
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={
                'user_id': current_user["id"],
                'membership_type': payment_data.membership_type
            }
        )
        
        return {
            "client_secret": intent.client_secret,
            "amount": amount
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/membership/webhook")
async def stripe_webhook(request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        user_id = payment_intent['metadata']['user_id']
        membership_type = payment_intent['metadata']['membership_type']
        
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user:
            user.membership_type = membership_type
            db.commit()
    
    return {"status": "success"}

@app.on_event("startup")
async def startup_event():
    init_database()
