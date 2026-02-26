# News Portal Backend (FastAPI + Supabase + Cloudinary)

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/fastapi-0.133.1-orange.svg)]()
[![Uvicorn](https://img.shields.io/badge/uvicorn-0.41.0-lightgrey.svg)]()

## Overview

This is a minimal **FastAPI** backend for a news portal. It uses **Supabase PostgreSQL** for storing news articles and **Cloudinary** for uploading and managing news images. The API provides full **CRUD** operations for news, including creating, reading, updating (PUT/PATCH), and deleting articles, along with pagination, search, and category filtering. Swagger and ReDoc documentation are included for easy testing and exploration of the endpoints.

---

## Live Demo

* **API Endpoint**: [https://news-portal-fastapi-server.vercel.app/news](https://news-portal-fastapi-server.vercel.app/news)
* **Swagger UI**: [https://news-portal-fastapi-server.vercel.app/docs](https://news-portal-fastapi-server.vercel.app/docs)
* **ReDoc Docs**: [https://news-portal-fastapi-server.vercel.app/redoc](https://news-portal-fastapi-server.vercel.app/redoc)

---

## Features

* Create news articles with optional image upload
* List news with pagination, search, and category filter
* Update news fully (PUT) or partially (PATCH)
* Delete news by ID
* Cloudinary integration for real image hosting

---

## Endpoints

| Method | Path              | Description                                                                 |
| ------ | ----------------- | --------------------------------------------------------------------------- |
| GET    | `/news`           | List news with optional query params: `page`, `limit`, `category`, `search` |
| GET    | `/news/{news_id}` | Fetch a single news item by ID                                              |
| POST   | `/news`           | Create a news article (supports image upload via `multipart/form-data`)     |
| PUT    | `/news/{news_id}` | Update all fields of a news item, including image                           |
| PATCH  | `/news/{news_id}` | Update specific fields of a news item                                       |
| DELETE | `/news/{news_id}` | Delete a news item by ID                                                    |

---

## Installation

1. **Clone repository**

```bash
git clone https://github.com/anis191/news-portal-fastapi.git
cd news-portal-fastapi-server
```

2. **Create virtual environment and activate**

```bash
python -m venv .env
# Windows
.env\Scripts\activate
# macOS/Linux
source .env/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
   Create a `.env` file (or copy `.env.example`) and add:

```
DATABASE_URL=postgresql://postgres:<PASSWORD>@<HOST>:5432/postgres
CLOUDINARY_CLOUD_NAME=<your_cloud_name>
CLOUDINARY_API_KEY=<your_api_key>
CLOUDINARY_API_SECRET=<your_api_secret>
```

---

## Running Locally

```bash
uvicorn main:app --reload
```

* The API will be accessible at [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Swagger docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* ReDoc docs: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Upload Images

* Upload images with POST `/news` or PUT `/news/{news_id}` endpoints using `multipart/form-data`.
* Images are automatically stored in Cloudinary under the `news_images` folder.

---

## Populate Sample Data

You can seed 15 news articles locally using:

```bash
python seed_news.py
```

> By default, images are `NULL`. You can later upload real images using the update endpoints.

---

## Project Structure

```
.
├── main.py           # FastAPI application
├── seed_news.py      # Populate sample news data
├── requirements.txt  # Python dependencies
├── .env.example      # Example environment variables
└── README.md
```

---

## Tech Stack

* **Backend:** FastAPI
* **Database:** PostgreSQL via Supabase
* **Image Hosting:** Cloudinary
* **Deployment:** Vercel (serverless FastAPI)

---

## 📌 License

MIT License. See [LICENSE](LICENSE).

---