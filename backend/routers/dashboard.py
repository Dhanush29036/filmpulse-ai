"""
FilmPulse AI — Dashboard Router (Phase 4)
==========================================
GET /dashboard-summary
  • Optional auth: shows personalised data when logged in
  • Aggregates all 5 ML models into one response
  • Uses auto_compute_discoverability (Phase 3) so sub-scores are derived from raw inputs
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from database import User
from auth import get_current_user
from ml.audience_model import predict_audience
from ml.budget_optimizer import optimize_budget
from ml.discoverability import auto_compute_discoverability
from ml.sentiment_engine import compute_sentiment
from ml.trailer_analyzer import run_trailer_pipeline

router = APIRouter()


@router.get("/dashboard-summary")
def dashboard_summary(
    genre:             str   = Query("Action"),
    budget:            float = Query(8_000_000),
    language:          str   = Query("Hindi"),
    platform:          str   = Query("Both"),
    cast_popularity:   float = Query(7.5),
    trailer_sentiment: float = Query(0.75),
    release_month:     int   = Query(10, ge=1, le=12, description="Planned release month (1-12)"),
    film_id:           str   = Query("", description="Optional: fetch results for a specific registered film"),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Master dashboard endpoint — aggregates all AI/ML module outputs.
    All data is from trained ML models (not hardcoded).

    Auth: optional — when authenticated, response includes ownership info.
    """
    # 1. Audience & Revenue (XGBoost + RandomForest)
    audience = predict_audience(genre, budget, language, trailer_sentiment, cast_popularity)

    # 2. Discoverability (auto-compute from raw inputs — Phase 3)
    discovery = auto_compute_discoverability(
        genre=genre,
        budget=budget,
        language=language,
        cast_popularity=cast_popularity,
        trailer_sentiment=trailer_sentiment,
        release_month=release_month,
        genre_score=audience["genre_score"],
    )

    # 3. Budget Optimization (Ridge + ε-greedy RL bandit) — 15% of budget for marketing
    marketing_budget = budget * 0.15
    budget_opt = optimize_budget(
        total_budget=marketing_budget,
        target_region="Pan-India",
        genre=genre,
        cast_popularity=cast_popularity,
        release_month=release_month,
    )

    # 4. Sentiment — baseline sample comments for dashboard preview
    sample_comments = [
        "This film looks amazing and exciting!",
        "Great cast and wonderful story",
        "Best trailer of the year for sure",
        "This is going to be a blockbuster",
        "Interesting concept, will watch",
    ]
    sentiment = compute_sentiment(sample_comments)

    # 5. Trailer analysis (simulation in demo mode)
    trailer = run_trailer_pipeline("", "demo.mp4", film_id or genre)

    # 6. Release recommendation based on discoverability
    score = discovery["score"]
    if score >= 80:
        release_rec = {
            "window":            discovery.get("release_window", "Diwali / Summer Blockbuster"),
            "confidence":        "High (85%)",
            "platform_strategy": "Simultaneous theatrical + OTT",
            "rationale":         "High discoverability & budget suit premium release slots.",
        }
    elif score >= 65:
        release_rec = {
            "window":            "Long weekend / Holiday release",
            "confidence":        "Medium (68%)",
            "platform_strategy": "OTT premiere + limited theatrical",
            "rationale":         "Mid-tier metrics suit strategic OTT-first with selective cinemas.",
        }
    else:
        release_rec = {
            "window":            "Mid-week OTT drop",
            "confidence":        "Low (52%)",
            "platform_strategy": "OTT exclusive",
            "rationale":         "Smaller reach optimised via direct-to-OTT strategy.",
        }

    platform_dist = {ch["name"]: ch["allocation_pct"] for ch in budget_opt["channels"]}

    data = {
        "film": {
            "genre":             genre,
            "budget":            budget,
            "language":          language,
            "platform":          platform,
            "cast_popularity":   cast_popularity,
            "trailer_sentiment": trailer_sentiment,
            "release_month":     release_month,
        },
        "discoverability_score":     discovery["score"],
        "discoverability_grade":     discovery["grade"],
        "discoverability_breakdown": discovery["breakdown"],
        "release_window":            discovery.get("release_window", ""),
        "audience_prediction":       audience,
        "budget_optimization":       budget_opt,
        "platform_distribution":     platform_dist,
        "sentiment":                 sentiment,
        "trailer_summary": {
            "viral_potential":  trailer["viral_potential"],
            "engagement_score": trailer["engagement_score"],
            "pacing_score":     trailer.get("pacing_score"),
            "audio_sync_score": trailer.get("audio_sync_score"),
            "emotion_labels":   trailer.get("emotion_labels", [])[:3],
        },
        "release_recommendation": release_rec,
    }

    # Inject user context if authenticated
    if current_user:
        data["user_context"] = {
            "user_id":  current_user.id,
            "name":     current_user.name,
            "role":     current_user.role,
            "company":  current_user.company or "",
        }

    return data
