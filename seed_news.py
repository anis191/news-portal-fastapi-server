# seed_news.py
from datetime import datetime
from sqlmodel import Session
from main import News, engine

# -----------------------
# 15 sample news items
# -----------------------
sample_news = [
    {
        "title": "AI Revolutionizes Healthcare",
        "description": "Artificial intelligence is transforming diagnostics and patient care worldwide.",
        "snippet": "AI helps doctors detect diseases faster and more accurately.",
        "url": "https://example.com/ai-healthcare",
        "imageUrl": None,
        "language": "en",
        "published_at": datetime.utcnow(),
        "source": "TechDaily",
        "categories": "Technology,Health"
    },
    {
        "title": "Global Economy Updates",
        "description": "Latest trends in the global economy and financial markets.",
        "snippet": "Stock markets see slight recovery amid inflation concerns.",
        "url": "https://example.com/economy-update",
        "imageUrl": None,
        "language": "en",
        "published_at": datetime.utcnow(),
        "source": "FinanceWorld",
        "categories": "Economy,Finance"
    },
    {
        "title": "New Species Discovered in Amazon",
        "description": "Scientists have discovered a new species of frog in the Amazon rainforest.",
        "snippet": "A rare discovery highlights biodiversity in the rainforest.",
        "url": "https://example.com/amazon-frog",
        "imageUrl": None,
        "language": "en",
        "published_at": datetime.utcnow(),
        "source": "NatureNews",
        "categories": "Science,Environment"
    },
    {
        "title": "SpaceX Launches New Satellite",
        "description": "SpaceX successfully launched a new communication satellite into orbit.",
        "snippet": "The launch marks another milestone for private space companies.",
        "url": "https://example.com/spacex-launch",
        "imageUrl": None,
        "language": "en",
        "published_at": datetime.utcnow(),
        "source": "SpaceToday",
        "categories": "Science,Technology"
    },
    {
        "title": "Breakthrough in Renewable Energy",
        "description": "Researchers have developed a more efficient solar panel technology.",
        "snippet": "This innovation could significantly reduce energy costs worldwide.",
        "url": "https://example.com/renewable-energy",
        "imageUrl": None,
        "language": "en",
        "published_at": datetime.utcnow(),
        "source": "EcoWorld",
        "categories": "Environment,Technology"
    },
]

# Add 10 more placeholder news to reach 15
for i in range(6, 16):
    sample_news.append({
        "title": f"Sample News Title {i}",
        "description": f"This is a description for news item {i}.",
        "snippet": f"Snippet for news {i}.",
        "url": f"https://example.com/news-{i}",
        "imageUrl": None,
        "language": "en",
        "published_at": datetime.utcnow(),
        "source": f"Source{i}",
        "categories": "General"
    })

# -----------------------
# Insert into database
# -----------------------
with Session(engine) as session:
    for news_data in sample_news:
        news_item = News(**news_data)
        session.add(news_item)
    session.commit()

print(f"Inserted {len(sample_news)} news items successfully!")