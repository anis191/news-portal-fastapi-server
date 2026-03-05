from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Body, Depends, Request
from sqlmodel import SQLModel, Field, create_engine, Session, select
from dotenv import load_dotenv
import os
import cloudinary
import cloudinary.uploader
from starlette.middleware.sessions import SessionMiddleware

# --- Load environment variables ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Admin credentials and session secret
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "change-me-in-prod")

# --- Connect to Supabase PostgreSQL ---
engine = create_engine(DATABASE_URL, echo=True)

# --- Cloudinary Settings ---
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# --- News model ---
class News(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    snippet: Optional[str] = None
    url: Optional[str] = None
    imageUrl: Optional[str] = None
    language: Optional[str] = "en"
    published_at: Optional[datetime] = None
    source: Optional[str] = None
    categories: Optional[str] = None  # comma separated

# --- Create table in Supabase ---
SQLModel.metadata.create_all(engine)

# --- Initialize FastAPI ---
app = FastAPI(title="News API (FastAPI + Supabase + Cloudinary)")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("ADMIN_SECRET_KEY"))

# --- CORS Middleware ---
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper function for filtering ---
def filter_news(items: List[News], category: Optional[str], search: Optional[str]):
    filtered = items
    if search:
        q = search.lower()
        filtered = [
            n for n in filtered
            if (n.title and q in n.title.lower()) or
               (n.description and q in n.description.lower()) or
               (n.snippet and q in n.snippet.lower())
        ]
    if category:
        filtered = [
            n for n in filtered
            if n.categories and category.lower() in n.categories.lower()
        ]
    return filtered

# --- Admin dependency ---
def admin_required(request: Request):
    """Ensure admin is logged in via session"""
    if not request.session.get("token") == "admin_logged_in":
        raise HTTPException(status_code=403, detail="Admin privileges required")

# --- News Endpoints ---
@app.get("/news", response_model=List[News])
def list_news(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    """List news sorted by newest first, with filtering and pagination optimized"""
    with Session(engine) as session:
        query = select(News).order_by(News.published_at.desc())

        # Filter by category (if provided)
        if category:
            query = query.where(News.categories.ilike(f"%{category}%"))

        # Filter by search (if provided)
        if search:
            q = f"%{search}%"
            query = query.where(
                (News.title.ilike(q)) |
                (News.description.ilike(q)) |
                (News.snippet.ilike(q))
            )

        # Pagination
        all_news = session.exec(
            query.offset((page - 1) * limit).limit(limit)
        ).all()

    return all_news

@app.get("/news/{news_id}", response_model=News)
def get_news(news_id: int):
    """Get a single news item by ID"""
    with Session(engine) as session:
        news = session.get(News, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news

@app.post("/news", response_model=News, status_code=201, dependencies=[Depends(admin_required)])
async def create_news(
    title: str = Form(...),
    description: str = Form(...),
    snippet: str = Form(None),
    url: str = Form(None),
    language: str = Form("en"),
    source: str = Form(None),
    categories: str = Form(None),
    image: UploadFile = File(None)
):
    """Create news with optional image upload, admin only"""
    image_url = None
    if image:
        result = cloudinary.uploader.upload(image.file, folder="news_images")
        image_url = result.get("secure_url")
    
    published_at_dt = datetime.utcnow()
    news_item = News(
        title=title,
        description=description,
        snippet=snippet,
        url=url,
        imageUrl=image_url,
        language=language,
        published_at=published_at_dt,
        source=source,
        categories=categories
    )

    with Session(engine) as session:
        session.add(news_item)
        session.commit()
        session.refresh(news_item)
    
    return news_item

@app.put("/news/{news_id}", response_model=News, dependencies=[Depends(admin_required)])
async def update_news(
    news_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    snippet: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    categories: Optional[str] = Form(None),
    image: UploadFile = File(None)
):
    """Update news fields and optionally replace image (admin only)"""
    with Session(engine) as session:
        news = session.get(News, news_id)
        if not news:
            raise HTTPException(status_code=404, detail="News not found")
        
        if title: news.title = title
        if description: news.description = description
        if snippet: news.snippet = snippet
        if url: news.url = url
        if language: news.language = language
        if source: news.source = source
        if categories: news.categories = categories

        if image:
            result = cloudinary.uploader.upload(image.file, folder="news_images")
            news.imageUrl = result.get("secure_url")
        
        session.add(news)
        session.commit()
        session.refresh(news)
    
    return news

@app.patch("/news/{news_id}", response_model=News, dependencies=[Depends(admin_required)])
async def patch_news(news_id: int, updated_data: dict = Body(...)):
    """Update one or few fields of a news item (admin only)"""
    with Session(engine) as session:
        news = session.get(News, news_id)
        if not news:
            raise HTTPException(status_code=404, detail="News not found")
        for key, value in updated_data.items():
            if hasattr(news, key):
                setattr(news, key, value)
        session.add(news)
        session.commit()
        session.refresh(news)
    return news

@app.delete("/news/{news_id}", status_code=204, dependencies=[Depends(admin_required)])
def delete_news(news_id: int):
    """Delete a news item by ID (admin only)"""
    with Session(engine) as session:
        news = session.get(News, news_id)
        if not news:
            raise HTTPException(status_code=404, detail="News not found")
        session.delete(news)
        session.commit()
    return {"detail": "News deleted successfully"}

# Admin Panel Setup:
import asyncio
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        if username == ADMIN_USER and password == ADMIN_PASS:
            request.session.update({"token": "admin_logged_in"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("token"))

# Initialize Admin
auth_backend = AdminAuth(secret_key=ADMIN_SECRET_KEY)
admin = Admin(app=app, engine=engine, authentication_backend=auth_backend, base_url="/admin")

# Register News model in Admin
class NewsAdmin(ModelView, model=News):
    column_list = [News.id, News.title, News.published_at, News.source, News.language]
    column_searchable_list = [News.title, News.description, News.snippet]
    column_filters = []
    form_excluded_columns = [News.id, News.published_at]

admin.add_view(NewsAdmin)
