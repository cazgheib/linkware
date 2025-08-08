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

users_db = {}
blog_posts_db = {}
memberships_db = {}
content_db = {}

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

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = users_db.get(user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user = users_db.get(user_id)
        return user
    except jwt.PyJWTError:
        return None

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/api/auth/register")
async def register(user_data: UserCreate):
    if any(user["email"] == user_data.email for user in users_db.values()):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    user = {
        "id": user_id,
        "email": user_data.email,
        "password": hashed_password,
        "full_name": user_data.full_name,
        "company": user_data.company,
        "membership_type": "free",
        "created_at": datetime.utcnow()
    }
    
    users_db[user_id] = user
    
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**{k: v for k, v in user.items() if k != "password"})
    }

@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    user = next((u for u in users_db.values() if u["email"] == user_data.email), None)
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user["id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**{k: v for k, v in user.items() if k != "password"})
    }

@app.post("/api/auth/google")
async def google_login(google_data: GoogleLogin):
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
        
        user = next((u for u in users_db.values() if u["email"] == email), None)
        
        if not user:
            user_id = str(uuid.uuid4())
            user = {
                "id": user_id,
                "email": email,
                "password": "",
                "full_name": name,
                "company": None,
                "membership_type": "free",
                "created_at": datetime.utcnow()
            }
            users_db[user_id] = user
        
        access_token = create_access_token(data={"sub": user["id"]})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": User(**{k: v for k, v in user.items() if k != "password"})
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
    current_user: dict = Depends(get_current_user)
):
    if membership_data.membership_type not in ["premium", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid membership type")
    
    current_user["membership_type"] = membership_data.membership_type
    users_db[current_user["id"]] = current_user
    
    return {"message": f"Membership upgraded to {membership_data.membership_type}"}

@app.get("/api/blog/posts")
async def get_blog_posts(
    category: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    posts = list(blog_posts_db.values())
    
    if current_user is None or current_user["membership_type"] == "free":
        posts = [post for post in posts if not post["is_premium"]]
    
    if category:
        posts = [post for post in posts if post["category"].lower() == category.lower()]
    
    posts.sort(key=lambda x: x["created_at"], reverse=True)
    
    return [BlogPost(**post) for post in posts]

@app.get("/api/blog/posts/{post_id}")
async def get_blog_post(post_id: str, current_user: Optional[dict] = Depends(get_current_user_optional)):
    post = blog_posts_db.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post["is_premium"] and (current_user is None or current_user["membership_type"] == "free"):
        raise HTTPException(status_code=403, detail="Premium membership required")
    
    return BlogPost(**post)

@app.post("/api/blog/posts")
async def create_blog_post(
    post_data: BlogPostCreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["membership_type"] == "free":
        raise HTTPException(status_code=403, detail="Premium membership required to create posts")
    
    post_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    post = {
        "id": post_id,
        "title": post_data.title,
        "content": post_data.content,
        "category": post_data.category,
        "tags": post_data.tags,
        "is_premium": post_data.is_premium,
        "author_id": current_user["id"],
        "created_at": now,
        "updated_at": now
    }
    
    blog_posts_db[post_id] = post
    
    return BlogPost(**post)

@app.get("/api/blog/categories")
async def get_blog_categories():
    categories = set()
    for post in blog_posts_db.values():
        categories.add(post["category"])
    return list(categories)

@app.get("/api/content/about")
async def get_about_content():
    about_content = content_db.get("about")
    if not about_content:
        raise HTTPException(status_code=404, detail="About content not found")
    return Content(**about_content)

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
    current_user: dict = Depends(get_current_user)
):
    if current_user["membership_type"] != "enterprise" or current_user["email"] != "admin@linkware.com":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    about_content = {
        "id": "about",
        "title": content_data.title,
        "content": content_data.content,
        "image_url": content_data.image_url,
        "updated_at": datetime.utcnow()
    }
    
    content_db["about"] = about_content
    
    return Content(**about_content)

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
async def stripe_webhook(request):
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
        
        if user_id in users_db:
            users_db[user_id]['membership_type'] = membership_type
    
    return {"status": "success"}

@app.on_event("startup")
async def startup_event():
    admin_id = str(uuid.uuid4())
    admin_user = {
        "id": admin_id,
        "email": "admin@linkware.com",
        "password": hash_password("admin123"),
        "full_name": "Linkware Consulting Admin",
        "company": "Linkware Consulting",
        "membership_type": "enterprise",
        "created_at": datetime.utcnow()
    }
    users_db[admin_id] = admin_user
    
    sample_posts = [
        {
            "title": "Introduction to Algorithmic Trading in Capital Markets",
            "content": "Algorithmic trading has revolutionized the way financial markets operate. This comprehensive guide covers the fundamentals of automated trading systems, their impact on market efficiency, and the technology stack required for implementation.",
            "category": "Trading Technology",
            "tags": ["algorithmic-trading", "fintech", "automation"],
            "is_premium": False
        },
        {
            "title": "Risk Management Systems: Building Robust Financial Infrastructure",
            "content": "Modern capital markets require sophisticated risk management systems to handle complex financial instruments and market volatility. Learn about real-time risk monitoring, stress testing, and regulatory compliance frameworks.",
            "category": "Risk Management",
            "tags": ["risk-management", "compliance", "infrastructure"],
            "is_premium": True
        },
        {
            "title": "Cloud Computing in Financial Services: Opportunities and Challenges",
            "content": "The adoption of cloud technologies in financial services presents both opportunities for innovation and challenges in security and compliance. Explore best practices for cloud migration in capital markets.",
            "category": "Cloud Technology",
            "tags": ["cloud-computing", "security", "fintech"],
            "is_premium": False
        }
    ]
    
    for post_data in sample_posts:
        post_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        post = {
            "id": post_id,
            "author_id": admin_id,
            "created_at": now,
            "updated_at": now,
            **post_data
        }
        
        blog_posts_db[post_id] = post
    
    default_about_content = {
        "id": "about",
        "title": "About Linkware Consulting",
        "content": """Welcome to Linkware Consulting, your trusted partner in IT solutions for capital markets.

Founded with a vision to bridge the gap between cutting-edge technology and financial services, we specialize in delivering innovative solutions that empower financial professionals to excel in today's dynamic markets.

Our Expertise:
• Algorithmic Trading Systems
• Risk Management Infrastructure  
• Cloud Computing Solutions
• Regulatory Compliance Technology
• Market Data Analytics
• High-Performance Computing

Our Mission:
To provide world-class technology consulting and educational resources that enable financial institutions and professionals to leverage the latest innovations in capital markets technology.

Our Team:
Our experienced consultants combine deep financial markets knowledge with technical expertise in modern software development, cloud architecture, and data analytics. We understand the unique challenges facing capital markets firms and deliver solutions that are both technically sound and business-focused.

Why Choose Linkware:
• Industry-specific expertise in capital markets technology
• Proven track record with leading financial institutions
• Commitment to innovation and best practices
• Comprehensive educational resources and thought leadership
• Flexible engagement models to meet your specific needs

Contact us today to learn how we can help transform your technology infrastructure and accelerate your business objectives.""",
        "image_url": None,
        "updated_at": datetime.utcnow()
    }
    
    content_db["about"] = default_about_content
