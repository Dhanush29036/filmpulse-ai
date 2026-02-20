"""
FilmPulse AI — MongoDB Layer (Phase 2)
---------------------------------------
Four MongoDB collections:
  1. trailer_analysis   → per-trailer ML scores, emotion curves, scene data
  2. social_comments    → raw social media comments per film
  3. sentiment_snapshots → hourly/daily aggregated sentiment state per film
  4. trend_history      → rolling buzz / hype trend over time per film

Uses PyMongo with a singleton client.
Falls back gracefully when MONGO_URL is not set.
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

# ── Connection ────────────────────────────────────────────────────────────────
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB   = os.getenv("MONGO_DB",  "filmpulse")

_client: Optional[MongoClient] = None


def get_mongo_client() -> Optional[MongoClient]:
    """Singleton MongoDB client. Returns None if Mongo is unavailable."""
    global _client
    if _client is None:
        try:
            _client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
            _client.admin.command("ping")  # fast connectivity check
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"[MongoDB] Not available: {e}. Mongo features will be disabled.")
            _client = None
    return _client


def get_mongo_db():
    """Return the FilmPulse MongoDB database, or None."""
    client = get_mongo_client()
    return client[MONGO_DB] if client else None


def init_mongo():
    """
    Ensure all MongoDB collections exist with their indexes.
    Called at app startup alongside init_db().
    """
    db = get_mongo_db()
    if db is None:
        print("[MongoDB] Skipping init — not connected.")
        return

    # ── Collection 1: trailer_analysis ───────────────────────────────────────
    ta = db["trailer_analysis"]
    ta.create_index([("film_id", ASCENDING)], background=True)
    ta.create_index([("created_at", DESCENDING)], background=True)
    ta.create_index([("film_id", ASCENDING), ("created_at", DESCENDING)],
                    name="idx_film_latest", background=True)

    # ── Collection 2: social_comments ────────────────────────────────────────
    sc = db["social_comments"]
    sc.create_index([("film_id", ASCENDING)], background=True)
    sc.create_index([("platform", ASCENDING)], background=True)
    sc.create_index([("created_at", DESCENDING)], background=True)
    sc.create_index([("sentiment_label", ASCENDING)], background=True)
    # TTL: auto-expire raw comments after 90 days
    sc.create_index([("created_at", ASCENDING)],
                    expireAfterSeconds=7_776_000,
                    name="ttl_comments_90d", background=True)

    # ── Collection 3: sentiment_snapshots ────────────────────────────────────
    ss = db["sentiment_snapshots"]
    ss.create_index([("film_id", ASCENDING)], background=True)
    ss.create_index([("timestamp", DESCENDING)], background=True)
    ss.create_index([("film_id", ASCENDING), ("timestamp", DESCENDING)],
                    name="idx_film_sentiment_ts", background=True)

    # ── Collection 4: trend_history ──────────────────────────────────────────
    th = db["trend_history"]
    th.create_index([("film_id", ASCENDING)], background=True)
    th.create_index([("date", DESCENDING)], background=True)
    th.create_index([("film_id", ASCENDING), ("date", DESCENDING)],
                    name="idx_film_trend_date", unique=True, background=True)

    print("[MongoDB] Collections and indexes initialized.")


# ══════════════════════════════════════════════════════════════════════════════
# COLLECTION 1 — trailer_analysis
# ══════════════════════════════════════════════════════════════════════════════
"""
Document schema:
{
  film_id:          str,        # matches Film.film_id in PostgreSQL
  filename:         str,
  viral_potential:  int,        # 0-100
  engagement_score: int,        # 0-100
  emotional_peak:   int,        # 0-100
  tension_index:    int,        # 0-100
  emotion_curve:    [int],      # list of 13 values (every 10s)
  scene_intensity:  [int],      # 7 scene-act values
  pacing_score:     float,      # avg seconds per cut
  audio_sync_score: int,        # 0-100
  meme_potential:   int,        # 0-100
  insights:         [str],      # narrative string list from ML
  model_version:    str,
  created_at:       datetime,
}
"""

def upsert_trailer_analysis(film_id: str, data: Dict[str, Any]) -> str:
    """Insert or replace the latest trailer analysis for a film."""
    db = get_mongo_db()
    if db is None:
        return ""
    doc = {
        "film_id":          film_id,
        "filename":         data.get("filename", ""),
        "viral_potential":  data.get("viral_potential", 0),
        "engagement_score": data.get("engagement_score", 0),
        "emotional_peak":   data.get("emotional_peak", 0),
        "tension_index":    data.get("tension_index", 0),
        "emotion_curve":    data.get("emotion_curve", []),
        "scene_intensity":  data.get("scene_intensity", []),
        "pacing_score":     data.get("pacing_score", 4.2),
        "audio_sync_score": data.get("audio_sync_score", 75),
        "meme_potential":   data.get("meme_potential", 0),
        "insights":         data.get("insights", []),
        "model_version":    data.get("model_version", "v1"),
        "created_at":       datetime.utcnow(),
    }
    result = db["trailer_analysis"].replace_one(
        {"film_id": film_id}, doc, upsert=True
    )
    return str(result.upserted_id or film_id)


def get_trailer_analysis(film_id: str) -> Optional[Dict]:
    """Get the latest trailer analysis for a film."""
    db = get_mongo_db()
    if db is None:
        return None
    doc = db["trailer_analysis"].find_one(
        {"film_id": film_id}, {"_id": 0}, sort=[("created_at", DESCENDING)]
    )
    return doc


# ══════════════════════════════════════════════════════════════════════════════
# COLLECTION 2 — social_comments
# ══════════════════════════════════════════════════════════════════════════════
"""
Document schema:
{
  film_id:         str,
  platform:        str,       # 'twitter'|'instagram'|'youtube'|'reddit'
  username:        str,
  text:            str,
  lang:            str,       # 'en'|'hi'|...
  sentiment_label: str,       # 'positive'|'neutral'|'negative'
  sentiment_score: float,     # -1.0 to +1.0
  likes:           int,
  shares:          int,
  source_url:      str,
  created_at:      datetime,  # TTL indexed (auto-expire 90 days)
  ingested_at:     datetime,
}
"""

def insert_social_comments(film_id: str, comments: List[Dict]) -> int:
    """Bulk-insert raw social comments for a film. Returns count inserted."""
    db = get_mongo_db()
    if db is None or not comments:
        return 0
    now = datetime.utcnow()
    docs = []
    for c in comments:
        docs.append({
            "film_id":         film_id,
            "platform":        c.get("platform", "unknown"),
            "username":        c.get("username", "anonymous"),
            "text":            c.get("text", ""),
            "lang":            c.get("lang", "en"),
            "sentiment_label": c.get("sentiment_label", "neutral"),
            "sentiment_score": c.get("sentiment_score", 0.0),
            "likes":           c.get("likes", 0),
            "shares":          c.get("shares", 0),
            "source_url":      c.get("source_url", ""),
            "created_at":      c.get("created_at", now),
            "ingested_at":     now,
        })
    result = db["social_comments"].insert_many(docs)
    return len(result.inserted_ids)


def get_social_comments(film_id: str, platform: Optional[str] = None,
                        sentiment: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """Fetch comments for a film, optionally filtered by platform/sentiment."""
    db = get_mongo_db()
    if db is None:
        return []
    query: Dict = {"film_id": film_id}
    if platform:
        query["platform"] = platform
    if sentiment:
        query["sentiment_label"] = sentiment
    cursor = db["social_comments"].find(
        query, {"_id": 0},
        sort=[("created_at", DESCENDING)],
        limit=limit
    )
    return list(cursor)


def get_comment_counts(film_id: str) -> Dict[str, int]:
    """Return pos/neu/neg comment counts for a film."""
    db = get_mongo_db()
    if db is None:
        return {"positive": 0, "neutral": 0, "negative": 0}
    pipeline = [
        {"$match": {"film_id": film_id}},
        {"$group": {"_id": "$sentiment_label", "count": {"$sum": 1}}}
    ]
    result = {r["_id"]: r["count"] for r in db["social_comments"].aggregate(pipeline)}
    return {
        "positive": result.get("positive", 0),
        "neutral":  result.get("neutral",  0),
        "negative": result.get("negative", 0),
    }


# ══════════════════════════════════════════════════════════════════════════════
# COLLECTION 3 — sentiment_snapshots
# ══════════════════════════════════════════════════════════════════════════════
"""
Document schema (hourly/daily aggregated snapshot):
{
  film_id:        str,
  timestamp:      datetime,    # when snapshot was taken
  period:         str,         # 'hourly'|'daily'
  hype_score:     float,       # 0-100
  positive_pct:   float,       # 0-100
  neutral_pct:    float,       # 0-100
  negative_pct:   float,       # 0-100
  total_analyzed: int,
  sentiment_label: str,        # 'Very Positive'|'Positive'|'Neutral'|'Negative'
  top_keywords:   [str],
  platforms:      {platform: count},
  model:          str,
}
"""

def save_sentiment_snapshot(film_id: str, snapshot: Dict) -> str:
    """Persist a sentiment snapshot for a film."""
    db = get_mongo_db()
    if db is None:
        return ""
    doc = {
        "film_id":         film_id,
        "timestamp":       datetime.utcnow(),
        "period":          snapshot.get("period", "hourly"),
        "hype_score":      snapshot.get("hype_score", 0),
        "positive_pct":    snapshot.get("positive_pct", 0),
        "neutral_pct":     snapshot.get("neutral_pct", 0),
        "negative_pct":    snapshot.get("negative_pct", 0),
        "total_analyzed":  snapshot.get("total_analyzed", 0),
        "sentiment_label": snapshot.get("sentiment_label", "Neutral"),
        "top_keywords":    snapshot.get("top_keywords", []),
        "platforms":       snapshot.get("platforms", {}),
        "model":           snapshot.get("model", "MultinomialNB+TF-IDF"),
    }
    result = db["sentiment_snapshots"].insert_one(doc)
    return str(result.inserted_id)


def get_sentiment_history(film_id: str, period: str = "daily", limit: int = 30) -> List[Dict]:
    """Return recent sentiment snapshots for a film (for timeseries chart)."""
    db = get_mongo_db()
    if db is None:
        return []
    cursor = db["sentiment_snapshots"].find(
        {"film_id": film_id, "period": period},
        {"_id": 0},
        sort=[("timestamp", DESCENDING)],
        limit=limit
    )
    return list(reversed(list(cursor)))   # chronological order


def get_latest_sentiment(film_id: str) -> Optional[Dict]:
    """Get the most recent sentiment snapshot for a film."""
    db = get_mongo_db()
    if db is None:
        return None
    return db["sentiment_snapshots"].find_one(
        {"film_id": film_id}, {"_id": 0}, sort=[("timestamp", DESCENDING)]
    )


# ══════════════════════════════════════════════════════════════════════════════
# COLLECTION 4 — trend_history
# ══════════════════════════════════════════════════════════════════════════════
"""
Document schema (one doc per film per day):
{
  film_id:            str,
  date:               str,       # "YYYY-MM-DD" — unique with film_id
  hype_score:         float,
  discoverability:    float,
  social_mentions:    int,        # total mentions across platforms
  positive_mentions:  int,
  negative_mentions:  int,
  google_trends_idx:  float,      # 0-100 (from Google Trends API or mock)
  youtube_views:      int,        # trailer views on day
  twitter_impressions:int,
  instagram_reach:    int,
  daily_delta_hype:   float,      # change vs previous day
  notes:              str,        # e.g. "Trailer drop", "Star interview"
  updated_at:         datetime,
}
"""

def upsert_trend_day(film_id: str, date: str, metrics: Dict) -> str:
    """Insert or update a single day's trend data for a film."""
    db = get_mongo_db()
    if db is None:
        return ""
    doc = {
        "$set": {
            "film_id":             film_id,
            "date":                date,
            "hype_score":          metrics.get("hype_score", 0),
            "discoverability":     metrics.get("discoverability", 0),
            "social_mentions":     metrics.get("social_mentions", 0),
            "positive_mentions":   metrics.get("positive_mentions", 0),
            "negative_mentions":   metrics.get("negative_mentions", 0),
            "google_trends_idx":   metrics.get("google_trends_idx", 0),
            "youtube_views":       metrics.get("youtube_views", 0),
            "twitter_impressions": metrics.get("twitter_impressions", 0),
            "instagram_reach":     metrics.get("instagram_reach", 0),
            "daily_delta_hype":    metrics.get("daily_delta_hype", 0),
            "notes":               metrics.get("notes", ""),
            "updated_at":          datetime.utcnow(),
        }
    }
    result = db["trend_history"].update_one(
        {"film_id": film_id, "date": date}, doc, upsert=True
    )
    return str(result.upserted_id or f"{film_id}:{date}")


def get_trend_history(film_id: str, days: int = 30) -> List[Dict]:
    """Return the last N days of trend data for a film (chronological)."""
    db = get_mongo_db()
    if db is None:
        return []
    cursor = db["trend_history"].find(
        {"film_id": film_id}, {"_id": 0},
        sort=[("date", DESCENDING)],
        limit=days
    )
    return list(reversed(list(cursor)))


def get_trend_summary(film_id: str) -> Dict:
    """Return peak hype, avg discoverability, total mentions for a film."""
    db = get_mongo_db()
    if db is None:
        return {}
    pipeline = [
        {"$match": {"film_id": film_id}},
        {"$group": {
            "_id": "$film_id",
            "peak_hype":           {"$max": "$hype_score"},
            "avg_discoverability": {"$avg": "$discoverability"},
            "total_mentions":      {"$sum": "$social_mentions"},
            "total_youtube_views": {"$sum": "$youtube_views"},
            "data_points":         {"$sum": 1},
        }}
    ]
    result = list(db["trend_history"].aggregate(pipeline))
    return result[0] if result else {}
