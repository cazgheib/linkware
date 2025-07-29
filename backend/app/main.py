from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import bcrypt
import uuid
import stripe
import os

app = FastAPI(title="Linkware Consulting Platform", version="1.0.0")

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
    current_user: dict = Depends(get_current_user)
):
    posts = list(blog_posts_db.values())
    
    if current_user["membership_type"] == "free":
        posts = [post for post in posts if not post["is_premium"]]
    
    if category:
        posts = [post for post in posts if post["category"].lower() == category.lower()]
    
    posts.sort(key=lambda x: x["created_at"], reverse=True)
    
    return [BlogPost(**post) for post in posts]

@app.get("/api/blog/posts/{post_id}")
async def get_blog_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post = blog_posts_db.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post["is_premium"] and current_user["membership_type"] == "free":
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
