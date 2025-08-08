from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
import os
import json
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./linkware.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    company = Column(String, nullable=True)
    membership_type = Column(String, default="free", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    blog_posts = relationship("BlogPost", back_populates="author")

class BlogPost(Base):
    __tablename__ = "blog_posts"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    tags = Column(Text, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    author = relationship("User", back_populates="blog_posts")
    
    def get_tags(self):
        return json.loads(self.tags) if self.tags else []
    
    def set_tags(self, tags_list):
        self.tags = json.dumps(tags_list) if tags_list else "[]"

class Content(Base):
    __tablename__ = "content"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)

def init_database():
    create_tables()
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.email == "admin@linkware.com").first()
        if not admin_user:
            from app.main import hash_password
            
            admin_id = str(uuid.uuid4())
            admin_user = User(
                id=admin_id,
                email="admin@linkware.com",
                password=hash_password("admin123"),
                full_name="Linkware Consulting Admin",
                company="Linkware Consulting",
                membership_type="enterprise",
                created_at=datetime.utcnow()
            )
            db.add(admin_user)
            db.commit()
            
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
                
                blog_post = BlogPost(
                    id=post_id,
                    title=post_data["title"],
                    content=post_data["content"],
                    category=post_data["category"],
                    is_premium=post_data["is_premium"],
                    author_id=admin_id,
                    created_at=now,
                    updated_at=now
                )
                blog_post.set_tags(post_data["tags"])
                db.add(blog_post)
            
            default_about_content = Content(
                id="about",
                title="About Linkware Consulting",
                content="""Welcome to Linkware Consulting, your trusted partner in IT solutions for capital markets.

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
                image_url=None,
                updated_at=datetime.utcnow()
            )
            db.add(default_about_content)
            db.commit()
    finally:
        db.close()
