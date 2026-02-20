"""
FilmPulse AI — Trends & Real-Time Router (Phase 6)
===================================================
GET  /trends/{film_id}              — latest trend history (last 30 days)
GET  /trends/{film_id}/realtime     — trigger immediate one-shot collection
GET  /trends/{film_id}/sentiment    — latest sentiment snapshot
GET  /trends/google/{title}         — Google Trends for any search term
GET  /social/{film_id}/comments     — recent social comments (paginated)
POST /social/{film_id}/collect      — [Producer/Admin] manual trigger
"""
from fastapi import APIRouter, Query, Depends, BackgroundTasks, HTTPException
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from auth import get_current_user, require_producer_or_admin
from database import User, Film, get_db
from mongo_db import (
    get_trend_history,
    get_trend_summary,
    get_latest_sentiment,
    get_sentiment_history,
    get_social_comments,
    get_comment_counts,
)
from realtime_collector import (
    run_hourly_collection,
    fetch_google_trends,
    register_film_for_tracking,
)

router = APIRouter()


@router.get("/trends/{film_id}")
def get_film_trends(
    film_id: str,
    days: int = Query(30, ge=1, le=90),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Return up to 90 days of daily trend history for a film.
    Includes hype_score, google_trends_idx, youtube_views, social_mentions per day.
    """
    history = get_trend_history(film_id, days=days)
    summary = get_trend_summary(film_id)
    if not history:
        raise HTTPException(status_code=404, detail="No trend data found for this film. Trigger collection first.")
    return {
        "film_id":   film_id,
        "days":      days,
        "summary":   summary,
        "history":   history,
        "data_points": len(history),
        "last_updated": history[-1].get("updated_at") if history else None,
    }


@router.get("/trends/{film_id}/realtime")
def trigger_realtime_collection(
    film_id: str,
    film_title: str = Query(..., description="Film title to search on social platforms"),
    trailer_url: str = Query("", description="YouTube trailer URL (optional)"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(require_producer_or_admin),
):
    """
    [PRODUCER / ADMIN] Manually trigger real-time data collection for a film.
    Runs Twitter + YouTube fetching + sentiment snapshot as a background task.
    """
    # Register for ongoing cron tracking
    register_film_for_tracking(film_id, film_title, trailer_url)

    if background_tasks:
        background_tasks.add_task(
            run_hourly_collection,
            film_id=film_id,
            film_title=film_title,
            trailer_url=trailer_url,
        )
        return {
            "status":     "collection_queued",
            "film_id":    film_id,
            "film_title": film_title,
            "message":    "Real-time collection started. Check /trends/{film_id}/sentiment for results.",
            "timestamp":  datetime.utcnow().isoformat(),
        }
    else:
        # Synchronous fallback
        result = run_hourly_collection(film_id, film_title, trailer_url)
        return {"status": "collection_complete", **result}


@router.get("/trends/{film_id}/sentiment")
def get_film_sentiment_history(
    film_id: str,
    period: str  = Query("hourly", regex="^(hourly|daily)$"),
    limit:  int  = Query(24, ge=1, le=168),
):
    """
    Return sentiment snapshot history for a film.
    period=hourly (default): last 24 hours | period=daily: last 30 days
    """
    history = get_sentiment_history(film_id, period=period, limit=limit)
    latest  = get_latest_sentiment(film_id)
    return {
        "film_id":  film_id,
        "period":   period,
        "latest":   latest,
        "history":  history,
        "count":    len(history),
    }


@router.get("/trends/google/{title}")
def google_trends_lookup(
    title: str,
    timeframe: str = Query("now 7-d", description="pytrends timeframe string"),
):
    """
    Fetch Google Trends interest index for any search query.
    No auth required — useful for competitor research.
    """
    result = fetch_google_trends(film_title=title, timeframe=timeframe)
    return {"query": title, "timeframe": timeframe, **result}


@router.get("/social/{film_id}/comments")
def get_social_comments_endpoint(
    film_id:   str,
    platform:  Optional[str] = Query(None, regex="^(twitter|youtube|instagram|reddit)?$"),
    sentiment: Optional[str] = Query(None, regex="^(positive|neutral|negative)?$"),
    limit:     int = Query(50, ge=1, le=200),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Paginated social comments for a film from MongoDB.
    Filter by platform (twitter|youtube) and/or sentiment (positive|neutral|negative).
    """
    comments = get_social_comments(film_id, platform=platform, sentiment=sentiment, limit=limit)
    counts   = get_comment_counts(film_id)
    return {
        "film_id":  film_id,
        "filters":  {"platform": platform, "sentiment": sentiment},
        "counts":   counts,
        "comments": comments,
        "returned": len(comments),
    }


@router.post("/social/{film_id}/collect")
def manual_collect(
    film_id:     str,
    film_title:  str = Query(""),
    trailer_url: str = Query(""),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(require_producer_or_admin),
    db: Session = Depends(get_db),
):
    """
    [PRODUCER / ADMIN] On-demand collection trigger.
    film_title is optional — auto-looked up from the DB when not provided.
    """
    # Auto-lookup film title if not provided by the client
    if not film_title:
        db_film = db.query(Film).filter(Film.film_id == film_id).first()
        if db_film:
            film_title = db_film.title
            trailer_url = trailer_url or ""
        else:
            raise HTTPException(status_code=404, detail=f"Film '{film_id}' not found. Provide film_title manually.")

    register_film_for_tracking(film_id, film_title, trailer_url)
    if background_tasks:
        background_tasks.add_task(run_hourly_collection, film_id, film_title, trailer_url)
        return {"status": "queued", "film_id": film_id, "film_title": film_title}
    result = run_hourly_collection(film_id, film_title, trailer_url)
    return {"status": "done", **result}
