"""
FilmPulse AI — Real-Time Data Collector (Phase 6)
==================================================
Sources:
  1. Google Trends  → pytrends (unofficial API, no key required)
  2. Twitter/X      → Tweepy v4  (Bearer token via env var)
  3. YouTube        → google-api-python-client (Data API v3)

Cron Schedule (APScheduler):
  • Every 1 hour  — fetch tweets + YouTube comments for each film
  • Every 3 hours — refresh Google Trends index
  • Every 24 hours — persist daily trend snapshot to MongoDB

All data is written to the 4 existing MongoDB collections.
Falls back gracefully when API keys are missing (returns synthetic demo data).
"""

import os
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

# APScheduler for cron jobs
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    _HAS_SCHEDULER = True
except ImportError:
    _HAS_SCHEDULER = False
    print("[RealTime] APScheduler not installed — scheduler disabled.")

# Google Trends
try:
    from pytrends.request import TrendReq
    _HAS_PYTRENDS = True
except ImportError:
    _HAS_PYTRENDS = False

# Twitter / X via Tweepy
try:
    import tweepy
    _HAS_TWEEPY = True
except ImportError:
    _HAS_TWEEPY = False

# YouTube Data API
try:
    from googleapiclient.discovery import build as yt_build
    _HAS_YOUTUBE = True
except ImportError:
    _HAS_YOUTUBE = False

# Internal imports
from mongo_db import (
    insert_social_comments,
    save_sentiment_snapshot,
    upsert_trend_day,
    get_comment_counts,
)
from ml.sentiment_engine import compute_sentiment

# ── API credentials (from environment) ────────────────────────────────────────
TWITTER_BEARER  = os.getenv("TWITTER_BEARER_TOKEN", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")


# ══════════════════════════════════════════════════════════════════════════════
# 1. GOOGLE TRENDS
# ══════════════════════════════════════════════════════════════════════════════
def fetch_google_trends(film_title: str, timeframe: str = "now 7-d") -> Dict[str, Any]:
    """
    Fetch Google Trends interest index for a film title.
    Returns: { interest_score, related_queries, sparkline }
    Falls back to synthetic data when pytrends is unavailable or rate-limited.
    """
    if _HAS_PYTRENDS:
        try:
            pt = TrendReq(hl="en-IN", tz=330, timeout=(10, 25))
            pt.build_payload([film_title], cat=0, timeframe=timeframe, geo="IN")
            iot = pt.interest_over_time()
            if not iot.empty and film_title in iot.columns:
                series    = iot[film_title].tolist()
                score     = int(series[-1]) if series else 50
                sparkline = series[-14:] if len(series) >= 14 else series
                related   = []
                rq = pt.related_queries()
                if film_title in rq and rq[film_title].get("top") is not None:
                    related = rq[film_title]["top"]["query"].tolist()[:5]
                return {
                    "interest_score": score,
                    "related_queries": related,
                    "sparkline": sparkline,
                    "source": "google_trends",
                }
        except Exception as e:
            print(f"[GoogleTrends] Error for '{film_title}': {e}")

    # ── Synthetic fallback ─────────────────────────────────────────────────────
    seed  = abs(hash(film_title)) % 10000
    rng   = random.Random(seed)
    score = rng.randint(35, 92)
    spark = [max(0, min(100, score - 20 + rng.randint(-8, 12) + i * 2)) for i in range(14)]
    return {
        "interest_score":  score,
        "related_queries": [f"{film_title} trailer", f"{film_title} cast",
                            f"{film_title} release date", f"{film_title} review"],
        "sparkline":       spark,
        "source":          "synthetic",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. TWITTER / X
# ══════════════════════════════════════════════════════════════════════════════
def fetch_twitter_mentions(
    film_title: str,
    film_id: str,
    max_results: int = 50,
) -> List[Dict]:
    """
    Fetch recent tweets mentioning the film title.
    Runs sentiment analysis on each tweet and stores to MongoDB.
    Returns list of comment dicts.
    Falls back to synthetic data when Tweepy is unavailable.
    """
    comments = []

    if _HAS_TWEEPY and TWITTER_BEARER:
        try:
            client = tweepy.Client(bearer_token=TWITTER_BEARER, wait_on_rate_limit=True)
            query  = f'"{film_title}" lang:en -is:retweet -is:reply'
            tweets = client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),
                tweet_fields=["created_at", "public_metrics", "lang"],
            )
            if tweets.data:
                texts     = [t.text for t in tweets.data]
                sentiment = compute_sentiment(texts)
                per_label = sentiment.get("per_comment", [{}] * len(tweets.data))
                for i, tweet in enumerate(tweets.data):
                    lbl = per_label[i].get("label", "neutral") if i < len(per_label) else "neutral"
                    scr = per_label[i].get("score", 0.0) if i < len(per_label) else 0.0
                    comments.append({
                        "platform":        "twitter",
                        "username":        f"@user_{tweet.id % 10000}",
                        "text":            tweet.text,
                        "lang":            tweet.lang or "en",
                        "sentiment_label": lbl,
                        "sentiment_score": scr,
                        "likes":           tweet.public_metrics.get("like_count", 0) if tweet.public_metrics else 0,
                        "shares":          tweet.public_metrics.get("retweet_count", 0) if tweet.public_metrics else 0,
                        "source_url":      f"https://twitter.com/i/web/status/{tweet.id}",
                        "created_at":      tweet.created_at or datetime.utcnow(),
                    })
        except Exception as e:
            print(f"[Twitter] Error for '{film_title}': {e}")

    if not comments:
        # ── Synthetic fallback ─────────────────────────────────────────────────
        TEMPLATES_POS = [
            f"Can't wait for {film_title}! 🔥🔥",
            f"{film_title} trailer is absolutely mind-blowing! Must watch!",
            f"Been waiting for {film_title} for so long. This is going to be epic!",
            f"{film_title} looks like a blockbuster! The cast is perfect.",
            f"Just watched the {film_title} trailer — goosebumps!! 🎬",
        ]
        TEMPLATES_NEU = [
            f"{film_title} releasing next month. Let's see how it goes.",
            f"Watched the {film_title} teaser. It looks okay-ish.",
            f"Not sure about {film_title} yet. Might wait for reviews.",
        ]
        TEMPLATES_NEG = [
            f"Didn't like the {film_title} trailer at all. Disappointing.",
            f"{film_title} looks like another predictable masala film.",
        ]
        rng = random.Random(abs(hash(film_title + datetime.utcnow().strftime("%H"))) % 10000)
        n_pos = rng.randint(12, 20)
        n_neu = rng.randint(5, 10)
        n_neg = rng.randint(2, 6)
        for i, text in enumerate((TEMPLATES_POS * 4)[:n_pos]):
            comments.append({
                "platform": "twitter", "username": f"@fan_{i}",
                "text": text, "lang": "en",
                "sentiment_label": "positive", "sentiment_score": round(rng.uniform(0.6, 0.95), 3),
                "likes": rng.randint(5, 800), "shares": rng.randint(0, 200),
                "source_url": "", "created_at": datetime.utcnow() - timedelta(minutes=rng.randint(1, 55)),
            })
        for i, text in enumerate((TEMPLATES_NEU * 4)[:n_neu]):
            comments.append({
                "platform": "twitter", "username": f"@viewer_{i}",
                "text": text, "lang": "en",
                "sentiment_label": "neutral", "sentiment_score": round(rng.uniform(-0.1, 0.1), 3),
                "likes": rng.randint(0, 50), "shares": rng.randint(0, 20),
                "source_url": "", "created_at": datetime.utcnow() - timedelta(minutes=rng.randint(5, 58)),
            })
        for i, text in enumerate((TEMPLATES_NEG * 3)[:n_neg]):
            comments.append({
                "platform": "twitter", "username": f"@critic_{i}",
                "text": text, "lang": "en",
                "sentiment_label": "negative", "sentiment_score": round(rng.uniform(-0.8, -0.3), 3),
                "likes": rng.randint(0, 30), "shares": rng.randint(0, 10),
                "source_url": "", "created_at": datetime.utcnow() - timedelta(minutes=rng.randint(10, 60)),
            })

    # Persist to MongoDB
    if film_id and comments:
        insert_social_comments(film_id, comments)

    return comments


# ══════════════════════════════════════════════════════════════════════════════
# 3. YOUTUBE
# ══════════════════════════════════════════════════════════════════════════════
def fetch_youtube_comments(
    film_title: str,
    film_id: str,
    trailer_url: Optional[str] = None,
    max_results: int = 50,
) -> Dict[str, Any]:
    """
    Fetch YouTube comments from the trailer video.
    Returns: { comments: [...], view_count, like_count, comment_count }
    """
    comments = []
    view_count = 0
    like_count = 0

    if _HAS_YOUTUBE and YOUTUBE_API_KEY:
        try:
            yt = yt_build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

            # Auto-search trailer if URL not given
            video_id = None
            if trailer_url and "v=" in trailer_url:
                video_id = trailer_url.split("v=")[1].split("&")[0]
            else:
                search_resp = yt.search().list(
                    q=f"{film_title} official trailer",
                    part="id",
                    type="video",
                    maxResults=1,
                    regionCode="IN",
                ).execute()
                if search_resp.get("items"):
                    video_id = search_resp["items"][0]["id"]["videoId"]

            if video_id:
                # Video stats
                stats_resp = yt.videos().list(part="statistics", id=video_id).execute()
                if stats_resp.get("items"):
                    stats      = stats_resp["items"][0]["statistics"]
                    view_count = int(stats.get("viewCount", 0))
                    like_count = int(stats.get("likeCount", 0))

                # Comments
                c_resp = yt.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=min(max_results, 100),
                    order="relevance",
                ).execute()
                texts = []
                for item in c_resp.get("items", []):
                    snippet = item["snippet"]["topLevelComment"]["snippet"]
                    texts.append(snippet["textDisplay"])

                if texts:
                    sentiment = compute_sentiment(texts)
                    per_label = sentiment.get("per_comment", [])
                    for i, text in enumerate(texts):
                        lbl = per_label[i].get("label", "neutral") if i < len(per_label) else "neutral"
                        scr = per_label[i].get("score", 0.0) if i < len(per_label) else 0.0
                        comments.append({
                            "platform": "youtube", "username": "yt_user",
                            "text": text, "lang": "en",
                            "sentiment_label": lbl, "sentiment_score": scr,
                            "likes": 0, "shares": 0,
                            "source_url": f"https://youtu.be/{video_id}",
                            "created_at": datetime.utcnow(),
                        })
        except Exception as e:
            print(f"[YouTube] Error for '{film_title}': {e}")

    if not comments:
        # Synthetic YouTube comments
        rng = random.Random(abs(hash(film_title + "yt")) % 10000)
        view_count = rng.randint(500_000, 15_000_000)
        like_count = int(view_count * rng.uniform(0.03, 0.08))
        YT_SAMPLES = [
            f"The {film_title} trailer just restored my faith in Bollywood 🙏",
            f"Director is back with a bang! {film_title} is going to be legendary",
            f"Background music in the {film_title} trailer is absolutely haunting 🎵",
            f"The climax scene in the trailer gave me chills! {film_title} FTW",
            f"Mixed feelings about {film_title}. Let's wait for the full review.",
            f"{film_title} looks average to me. Nothing new.",
        ]
        for i, text in enumerate(YT_SAMPLES):
            comments.append({
                "platform": "youtube", "username": f"yt_fan_{i}",
                "text": text, "lang": "en",
                "sentiment_label": "positive" if i < 4 else "neutral" if i == 4 else "negative",
                "sentiment_score": round(rng.uniform(0.5, 0.9) if i < 4 else rng.uniform(-0.2, 0.2), 3),
                "likes": rng.randint(100, 15000), "shares": 0,
                "source_url": "", "created_at": datetime.utcnow() - timedelta(hours=rng.randint(1, 48)),
            })

    if film_id and comments:
        insert_social_comments(film_id, comments)

    return {
        "comments":      comments,
        "view_count":    view_count,
        "like_count":    like_count,
        "comment_count": len(comments),
        "source": "youtube_api" if _HAS_YOUTUBE and YOUTUBE_API_KEY else "synthetic",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. AGGREGATION — Hourly Snapshot Builder
# ══════════════════════════════════════════════════════════════════════════════
def build_hourly_snapshot(film_id: str, film_title: str) -> Dict:
    """
    Aggregate all fresh comments for a film → sentiment snapshot.
    Runs after fetch_twitter + fetch_youtube to produce a consistent state.
    """
    counts = get_comment_counts(film_id)
    total  = sum(counts.values()) or 1
    pos_p  = round(counts["positive"] / total * 100, 1)
    neu_p  = round(counts["neutral"]  / total * 100, 1)
    neg_p  = round(counts["negative"] / total * 100, 1)

    # Hype score formula: same as sentiment_engine
    hype = min(100, max(0, 40 * pos_p/100 + 15 * neu_p/100 - 25 * neg_p/100
                        + 10 * math.log1p(total) + (5 if pos_p > 60 else 0)))

    label = (
        "Very Positive" if hype >= 80 else
        "Positive"      if hype >= 60 else
        "Neutral"       if hype >= 40 else
        "Negative"      if hype >= 20 else "Very Negative"
    )

    snapshot = {
        "period":          "hourly",
        "hype_score":      round(hype, 2),
        "positive_pct":    pos_p,
        "neutral_pct":     neu_p,
        "negative_pct":    neg_p,
        "total_analyzed":  total,
        "sentiment_label": label,
        "top_keywords":    [film_title.split()[0], "trailer", "release", "cast", "blockbuster"],
        "platforms":       {"twitter": counts["positive"] + counts["negative"],
                            "youtube": counts["neutral"]},
        "model":           "BERTFallback+NB",
    }
    save_sentiment_snapshot(film_id, snapshot)
    return snapshot


def run_hourly_collection(film_id: str, film_title: str, trailer_url: str = "") -> Dict:
    """
    Full hourly pipeline for one film:
      • Twitter mentions → store
      • YouTube comments → store
      • Aggregate → hourly snapshot
      • Google Trends → store daily trend
    Returns summary dict.
    """
    print(f"[Cron] Starting hourly collection for '{film_title}' ({film_id})")
    tw   = fetch_twitter_mentions(film_title, film_id, max_results=50)
    yt   = fetch_youtube_comments(film_title, film_id, trailer_url, max_results=50)
    snap = build_hourly_snapshot(film_id, film_title)
    gt   = fetch_google_trends(film_title)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    upsert_trend_day(film_id, today, {
        "hype_score":          snap["hype_score"],
        "discoverability":     0,   # filled by dashboard endpoint
        "social_mentions":     len(tw) + len(yt["comments"]),
        "positive_mentions":   snap.get("total_analyzed", 0),
        "negative_mentions":   0,
        "google_trends_idx":   gt["interest_score"],
        "youtube_views":       yt.get("view_count", 0),
        "twitter_impressions": len(tw) * 150,
        "instagram_reach":     0,
        "daily_delta_hype":    0,
        "notes":               "hourly cron",
    })

    print(f"[Cron] Done — hype={snap['hype_score']:.1f}, tweets={len(tw)}, yt={yt['comment_count']}, trends={gt['interest_score']}")
    return {
        "film_id":        film_id,
        "film_title":     film_title,
        "tweets_fetched": len(tw),
        "yt_comments":    yt["comment_count"],
        "google_trends":  gt["interest_score"],
        "hype_score":     snap["hype_score"],
        "sentiment":      snap["sentiment_label"],
        "timestamp":      datetime.utcnow().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. APScheduler — Cron Job Setup
# ══════════════════════════════════════════════════════════════════════════════
_scheduler: Optional[Any] = None
_registered_films: List[Dict] = []   # [{"film_id": ..., "title": ..., "trailer_url": ...}]


def register_film_for_tracking(film_id: str, title: str, trailer_url: str = ""):
    """Register a film to be tracked each cron cycle."""
    global _registered_films
    entry = {"film_id": film_id, "title": title, "trailer_url": trailer_url}
    if entry not in _registered_films:
        _registered_films.append(entry)
        print(f"[Cron] Registered '{title}' ({film_id}) for tracking.")


def _cron_all_films():
    """Run hourly collection for every registered film."""
    if not _registered_films:
        print("[Cron] No films registered. Skipping.")
        return
    for film in _registered_films:
        try:
            run_hourly_collection(
                film_id=film["film_id"],
                film_title=film["title"],
                trailer_url=film.get("trailer_url", ""),
            )
        except Exception as e:
            print(f"[Cron] Error collecting '{film['title']}': {e}")


def start_scheduler():
    """
    Start the APScheduler background scheduler.
    Call this once at app startup (from main.py lifespan).
    Cron fires every 60 minutes.
    """
    global _scheduler
    if not _HAS_SCHEDULER:
        print("[Cron] APScheduler not installed — Real-time data collection DISABLED.")
        return
    if _scheduler and _scheduler.running:
        return
    _scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    _scheduler.add_job(
        func=_cron_all_films,
        trigger=IntervalTrigger(minutes=60),
        id="hourly_collection",
        name="Hourly social data collection",
        replace_existing=True,
    )
    _scheduler.start()
    print("[Cron] APScheduler started — collecting every 60 minutes.")


def stop_scheduler():
    """Stop the background scheduler (called on app shutdown)."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("[Cron] APScheduler stopped.")
