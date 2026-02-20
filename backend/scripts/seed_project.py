
import sys
import os
import random
from datetime import datetime, timedelta

# Ensure we can import from the current directory
sys.path.insert(0, '.')

from database import init_db, SessionLocal, User, Film
from mongo_db import (
    init_mongo, 
    upsert_trend_day, 
    insert_social_comments, 
    save_sentiment_snapshot,
    upsert_trailer_analysis
)
from auth import hash_password

def seed_sql():
    print("--- Seeding SQL (PostgreSQL/SQLite) ---")
    db = SessionLocal()
    try:
        # 1. Create Admin User
        admin_email = "admin@filmpulse.ai"
        if not db.query(User).filter(User.email == admin_email).first():
            admin = User(
                email=admin_email,
                name="System Admin",
                company="FilmPulse HQ",
                hashed_password=hash_password("admin123"),
                role="admin",
                avatar_initials="SA"
            )
            db.add(admin)
            print(f"Created admin: {admin_email}")
        
        # 2. Create Sample Films
        films_data = [
            {
                "title": "Brahmastra: Part Two",
                "genre": "Action",
                "language": "Hindi",
                "budget": 2500000000, # 250 Cr
                "release_date": "2024-12-25",
                "platform": "Theatre",
                "director": "Ayan Mukerji",
                "cast_popularity": 9.2,
                "status": "analyzed"
            },
            {
                "title": "The Metro Files",
                "genre": "Thriller",
                "language": "Hindi",
                "budget": 450000000, # 45 Cr
                "release_date": "2024-05-10",
                "platform": "OTT",
                "director": "Vikramaditya Motwane",
                "cast_popularity": 7.5,
                "status": "registered"
            },
            {
                "title": "Desi Knights",
                "genre": "Comedy",
                "language": "Hindi",
                "budget": 800000000, # 80 Cr
                "release_date": "2024-08-15",
                "platform": "Theatre",
                "director": "Rohit Shetty",
                "cast_popularity": 8.5,
                "status": "analyzed"
            }
        ]
        
        for f_data in films_data:
            if not db.query(Film).filter(Film.title == f_data["title"]).first():
                film = Film(**f_data)
                db.add(film)
                print(f"Created film: {f_data['title']}")
        
        db.commit()
    except Exception as e:
        print(f"SQL Seed Error: {e}")
        db.rollback()
    finally:
        db.close()

def seed_mongo():
    print("--- Seeding MongoDB ---")
    db = SessionLocal()
    films = db.query(Film).all()
    db.close()

    if not films:
        print("No films found in SQL. Run seed_sql first.")
        return

    platforms = ["twitter", "youtube", "instagram"]
    sentiments = ["positive", "neutral", "negative"]
    
    for film in films:
        film_id = str(film.id)
        print(f"Seeding Mongo data for {film.title} (ID: {film_id})")

        # 1. Trend History (Last 10 Days)
        for i in range(10):
            date_str = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            metrics = {
                "hype_score": random.uniform(40, 95),
                "discoverability": random.uniform(50, 85),
                "social_mentions": random.randint(500, 5000),
                "youtube_views": random.randint(10000, 100000),
                "google_trends_idx": random.uniform(20, 100)
            }
            upsert_trend_day(film_id, date_str, metrics)

        # 2. Social Comments
        comments = []
        templates = {
            "positive": ["Can't wait!", "Amazing trailer", "VFX look top notch", "Day 1 booking confirmed!"],
            "neutral": ["Interesting concept", "Waiting for more details", "The cast looks okay"],
            "negative": ["Looks like a copy", "Waste of budget", "Not my type of movie", "Disappointing teaser"]
        }
        
        for _ in range(50):
            s_label = random.choice(sentiments)
            comments.append({
                "platform": random.choice(platforms),
                "username": f"user_{random.randint(1000, 9999)}",
                "text": random.choice(templates[s_label]),
                "sentiment_label": s_label,
                "sentiment_score": 0.8 if s_label == "positive" else (-0.8 if s_label == "negative" else 0.0),
                "likes": random.randint(0, 100),
                "created_at": datetime.utcnow() - timedelta(hours=random.randint(1, 48))
            })
        insert_social_comments(film_id, comments)

        # 3. Latest Sentiment Snapshot
        save_sentiment_snapshot(film_id, {
            "hype_score": 75.5,
            "period": "hourly",
            "positive_pct": 60,
            "neutral_pct": 25,
            "negative_pct": 15,
            "total_analyzed": 50
        })

if __name__ == "__main__":
    print("Starting Project Seeding...")
    init_db()
    init_mongo()
    seed_sql()
    seed_mongo()
    print("Project Seeding COMPLETE.")
