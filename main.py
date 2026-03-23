from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Body, Depends, Request
from sqlmodel import SQLModel, Field, create_engine, Session, select
from sqlalchemy import event
from sqlalchemy.orm import Session as SASession
from dotenv import load_dotenv
import os
import cloudinary
import cloudinary.uploader
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend

# --- Load environment variables ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
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

# --- News Model ---
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
    categories: Optional[str] = None
    is_featured: bool = Field(default=False)


# --- SQLAlchemy Event Listener ---
# Enforces only one featured news at a time.
# Fires on ANY write — FastAPI endpoints AND sqladmin panel.
@event.listens_for(SASession, "before_flush")
def enforce_single_featured(session, flush_context, instances):
    for obj in list(session.new) + list(session.dirty):
        if not isinstance(obj, News):
            continue
        if not obj.is_featured:
            continue
        already_featured = session.execute(
            select(News).where(News.is_featured == True)
        ).scalars().all()
        for other in already_featured:
            if other.id != obj.id:
                other.is_featured = False
                session.add(other)


# --- Create Tables ---
SQLModel.metadata.create_all(engine)

# --- Initialize FastAPI ---
app = FastAPI(title="News API (FastAPI + Supabase + Cloudinary)")

# --- Middlewares ---
app.add_middleware(SessionMiddleware, secret_key=ADMIN_SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Admin Dependency ---
def admin_required(request: Request):
    if not request.session.get("token") == "admin_logged_in":
        raise HTTPException(status_code=403, detail="Admin privileges required")


# ===========================================================================
# NEWS ENDPOINTS
# IMPORTANT: Fixed-path routes (/news/featured/current) MUST be registered
# BEFORE dynamic-path routes (/news/{news_id}) to avoid routing conflicts.
# ===========================================================================

@app.get("/news", response_model=List[News])
def list_news(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    """List news sorted by newest first, with optional filtering and pagination"""
    with Session(engine) as session:
        query = select(News).order_by(News.published_at.desc())

        if category:
            query = query.where(News.categories.ilike(f"%{category}%"))

        if search:
            q = f"%{search}%"
            query = query.where(
                (News.title.ilike(q)) |
                (News.description.ilike(q)) |
                (News.snippet.ilike(q))
            )

        all_news = session.exec(
            query.offset((page - 1) * limit).limit(limit)
        ).all()

    return all_news


# ✅ FIXED PATH — must be registered BEFORE /news/{news_id}
@app.get("/news/featured/current", response_model=Optional[News])
def get_featured_news():
    """Get the currently featured news item (is_featured=True)"""
    with Session(engine) as session:
        news = session.exec(
            select(News).where(News.is_featured == True)
        ).first()
    return news


# ✅ DYNAMIC PATH — must always come AFTER all fixed /news/* routes
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
    is_featured: bool = Form(False),
    image: UploadFile = File(None)
):
    """Create a news item with optional image upload (admin only)"""
    image_url = None
    if image:
        result = cloudinary.uploader.upload(image.file, folder="news_images")
        image_url = result.get("secure_url")

    news_item = News(
        title=title,
        description=description,
        snippet=snippet,
        url=url,
        imageUrl=image_url,
        language=language,
        published_at=datetime.utcnow(),
        source=source,
        categories=categories,
        is_featured=is_featured
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
    is_featured: Optional[bool] = Form(None),
    image: UploadFile = File(None)
):
    """Update a news item and optionally replace its image (admin only)"""
    with Session(engine) as session:
        news = session.get(News, news_id)
        if not news:
            raise HTTPException(status_code=404, detail="News not found")

        if title:                       news.title = title
        if description:                 news.description = description
        if snippet:                     news.snippet = snippet
        if url:                         news.url = url
        if language:                    news.language = language
        if source:                      news.source = source
        if categories:                  news.categories = categories
        if is_featured is not None:     news.is_featured = is_featured

        if image:
            result = cloudinary.uploader.upload(image.file, folder="news_images")
            news.imageUrl = result.get("secure_url")

        session.add(news)
        session.commit()
        session.refresh(news)

    return news


@app.patch("/news/{news_id}", response_model=News, dependencies=[Depends(admin_required)])
async def patch_news(news_id: int, updated_data: dict = Body(...)):
    """Partially update a news item (admin only)"""
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


# ===========================================================================
# ADMIN PANEL
# ===========================================================================

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


auth_backend = AdminAuth(secret_key=ADMIN_SECRET_KEY)
admin = Admin(app=app, engine=engine, authentication_backend=auth_backend, base_url="/admin")


class NewsAdmin(ModelView, model=News):
    column_list = [News.id, News.title, News.published_at, News.source, News.language, News.is_featured]
    column_searchable_list = [News.title, News.description, News.snippet]
    column_filters = []
    form_excluded_columns = [News.id, News.published_at]


admin.add_view(NewsAdmin)