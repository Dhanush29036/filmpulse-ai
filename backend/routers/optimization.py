"""
FilmPulse AI — Budget Optimization & Release Recommendation Router (Phase 4)
==============================================================================
GET /budget-optimization
  • Auth: optional (returns extra context when logged in)
  • Role guard: NONE (public endpoint — demo-friendly)

GET /release-recommendation
  • Upgraded: now uses discoverability sub-scores + festival calendar

GET /what-if-simulation   ← NEW Phase 4 endpoint
  • Producer/Admin only
  • Dynamically recalculates revenue + discoverability when budget / release_date / platform changes
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from auth import get_current_user, require_producer_or_admin
from database import User
from ml.budget_optimizer import optimize_budget
from ml.audience_model import predict_audience
from ml.discoverability import auto_compute_discoverability

router = APIRouter()


@router.get("/budget-optimization")
def budget_optimization(
    total_budget:    float = Query(5_000_000, description="Total marketing budget in INR"),
    target_region:   str   = Query("Pan-India"),
    genre:           str   = Query("Action"),
    cast_popularity: float = Query(7.0),
    release_month:   int   = Query(10, ge=1, le=12),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    AI-powered marketing budget allocation across 8 channels.
    Uses Ridge Regression ROI model + ε-Greedy Multi-Arm Bandit (RL layer).
    """
    result = optimize_budget(
        total_budget=total_budget,
        target_region=target_region,
        genre=genre,
        cast_popularity=cast_popularity,
        release_month=release_month,
    )
    if current_user:
        result["requested_by"] = current_user.email
    return result


@router.get("/release-recommendation")
def release_recommendation(
    genre:           str   = Query("Action"),
    budget:          float = Query(8_000_000),
    language:        str   = Query("Hindi"),
    platform:        str   = Query("Both"),
    cast_popularity: float = Query(7.5),
    trailer_sentiment: float = Query(0.75),
    release_month:   int   = Query(10, ge=1, le=12),
):
    """
    Recommend optimal release window and platform strategy.
    Derives discoverability sub-scores from raw inputs via auto_compute_discoverability.
    """
    audience  = predict_audience(genre, budget, language, trailer_sentiment, cast_popularity)
    discovery = auto_compute_discoverability(
        genre=genre, budget=budget, language=language,
        cast_popularity=cast_popularity, trailer_sentiment=trailer_sentiment,
        release_month=release_month, genre_score=audience["genre_score"],
    )
    score = discovery["score"]

    # Festival windows map
    _FESTIVAL_MONTHS = {
        10: "Navratri / Pre-Diwali",
        11: "Diwali ⭐ (Peak Window)",
        12: "Christmas / New Year",
        1:  "Republic Day / Sankranti",
        3:  "Holi",
        6:  "Summer Vacation peak",
        8:  "Independence Day",
    }
    festival_tag = _FESTIVAL_MONTHS.get(release_month, f"Month {release_month}")

    if score >= 80:
        window    = f"Summer Blockbuster (May–Jun) / {festival_tag}"
        confidence = "High (85%)"
        strategy  = "Simultaneous theatrical + OTT"
        rationale = "High discoverability score & strong audience affinity — prime for premium slots."
    elif score >= 65:
        window    = f"Long weekend / {festival_tag}"
        confidence = "Medium (68%)"
        strategy  = "OTT premiere + limited theatrical"
        rationale = "Mid-tier metrics suit strategic OTT-first with selective cinemas."
    else:
        window    = "Mid-week OTT drop"
        confidence = "Low (52%)"
        strategy  = "OTT exclusive"
        rationale = "Smaller reach is best optimised via direct-to-OTT strategy."

    festivals = []
    if genre in ("Drama", "Thriller") and budget < 5_000_000:
        festivals = ["MAMI Mumbai Film Festival", "BIFF - Busan IFF", "IFFK Kerala"]

    return {
        "discoverability_score":    score,
        "discoverability_grade":    discovery["grade"],
        "release_window":           discovery.get("release_window", window),
        "recommended_window":       window,
        "festival_season":          festival_tag,
        "platform_strategy":        strategy,
        "confidence":               confidence,
        "rationale":                rationale,
        "festival_recommendations": festivals,
        "competitor_weeks_to_avoid": [
            "Week of major Hollywood releases",
            "IPL Final week",
            "World Cup Final weekend",
        ],
        "sub_scores": discovery.get("sub_score_inputs", {}),
        "audience_primary_age": audience["primary_age_group"],
        "revenue_estimate":     audience["revenue_estimate"],
    }


@router.get("/what-if-simulation")
def what_if_simulation(
    # Base film params
    genre:             str   = Query("Action"),
    language:          str   = Query("Hindi"),
    cast_popularity:   float = Query(7.5),
    trailer_sentiment: float = Query(0.75),
    # Variables to simulate
    budget:            float = Query(8_000_000,  description="Sim: total production budget (INR)"),
    release_month:     int   = Query(10, ge=1, le=12, description="Sim: release month (1-12)"),
    platform:          str   = Query("Both",     description="Sim: Theatre | OTT | Both"),
    marketing_pct:     float = Query(0.15, ge=0.05, le=0.40, description="Sim: % of budget for marketing"),
    current_user: User = Depends(require_producer_or_admin),
):
    """
    [PRODUCER / ADMIN] — What-If Simulation Mode.

    Dynamically recalculates:
      • Revenue prediction (XGBoost)
      • Discoverability score & grade
      • Budget allocation across 8 channels
      • Best release window

    Producer changes budget / release_date / platform and sees results instantly.
    This demonstrates deep business + AI thinking.
    """
    audience = predict_audience(
        genre=genre, budget=budget, language=language,
        trailer_sentiment=trailer_sentiment, cast_popularity=cast_popularity,
    )
    discovery = auto_compute_discoverability(
        genre=genre, budget=budget, language=language,
        cast_popularity=cast_popularity, trailer_sentiment=trailer_sentiment,
        release_month=release_month, genre_score=audience["genre_score"],
    )
    marketing_budget = budget * marketing_pct
    budget_opt = optimize_budget(
        total_budget=marketing_budget,
        target_region="Pan-India",
        genre=genre,
        cast_popularity=cast_popularity,
        release_month=release_month,
    )

    # OTT vs Theatre revenue split
    platform_multiplier = {"OTT": 0.60, "Theatre": 1.00, "Both": 0.85}.get(platform, 0.85)
    rev_mid_adj = round(audience["revenue_estimate"]["mid"] * platform_multiplier, 2)

    # Confidence delta based on discoverability
    base_conf = 0.55 + (discovery["score"] / 100) * 0.35
    rev_low   = round(rev_mid_adj * (base_conf - 0.12), 2)
    rev_high  = round(rev_mid_adj * (base_conf + 0.18), 2)

    score = discovery["score"]
    if score >= 80:
        rec_window = f"Summer / Diwali (Month {release_month})"
    elif score >= 65:
        rec_window = f"Long Weekend (Month {release_month})"
    else:
        rec_window = "Mid-week OTT drop"

    return {
        "simulation_inputs": {
            "budget":          budget,
            "release_month":   release_month,
            "platform":        platform,
            "marketing_pct":   marketing_pct,
            "genre":           genre,
            "language":        language,
            "cast_popularity": cast_popularity,
        },
        "results": {
            "discoverability_score": discovery["score"],
            "discoverability_grade": discovery["grade"],
            "release_window":        discovery.get("release_window", rec_window),
            "revenue_estimate": {
                "low":  rev_low,
                "mid":  rev_mid_adj,
                "high": rev_high,
                "unit": "million INR",
                "platform_adjustment": f"{int(platform_multiplier * 100)}% ({platform})",
            },
            "marketing_budget": round(marketing_budget),
            "top_channel":      budget_opt.get("top_channel", ""),
            "blended_roi":      budget_opt.get("blended_roi", 0),
            "audience_primary": audience["primary_age_group"],
            "region_probability": audience["region_probability"],
        },
        "sub_score_inputs":  discovery.get("sub_score_inputs", {}),
        "channel_allocation": [
            {"name": ch["name"], "pct": ch["allocation_pct"], "roi": ch["estimated_roi"]}
            for ch in budget_opt["channels"]
        ],
        "simulated_by": current_user.email,
    }
