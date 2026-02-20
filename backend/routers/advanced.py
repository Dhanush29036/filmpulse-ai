"""
FilmPulse AI — Advanced Features Router (Phase 8)
==================================================
All 8 Phase 8 endpoints:

  GET  /advanced/taglines            — Poster tagline variants (3 tones)
  GET  /advanced/captions            — Platform marketing captions (5 platforms)
  GET  /advanced/captions/ab-test    — A/B test caption pair
  GET  /advanced/competitors         — Competitor comparison vs historical films
  GET  /advanced/heatmap             — Regional audience heatmap (35 Indian states)
  GET  /advanced/festival-score      — Festival success probability (9 festivals)
  GET  /advanced/market-intelligence — Full compound intelligence report (all 5 engines)
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional, List
from sqlalchemy.orm import Session
from auth import get_current_user, require_producer_or_admin
from database import User, Film, get_db
from ml.caption_generator import (
    generate_taglines,
    generate_marketing_captions,
    generate_ab_test_captions,
)
from ml.competitor_engine import run_competitor_analysis
from ml.regional_heatmap  import generate_regional_heatmap
from ml.festival_scorer   import score_festival_probability

router = APIRouter(prefix="/advanced", tags=["Advanced AI"])


# ── 1. Poster Taglines ────────────────────────────────────────────────────────
@router.get("/taglines")
def get_taglines(
    film_title:    str   = Query(..., description="Film title"),
    genre:         str   = Query("Drama"),
    release_month: int   = Query(11, ge=1, le=12),
    director:      str   = Query("", description="Director name (optional)"),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Generate 3 poster taglines per tone (emotional / action / mystery).
    Returns 3 × 3 = 9 unique taglines tailored to genre & release timing.
    """
    taglines = generate_taglines(film_title, genre, release_month, director)
    total    = sum(len(v) for v in taglines.values())
    return {
        "film_title":    film_title,
        "genre":         genre,
        "release_month": release_month,
        "taglines":      taglines,
        "total":         total,
        "tip":           "Use emotional tagline for OOH/newspaper, action for digital, mystery for teaser.",
    }


# ── 2. Marketing Captions ─────────────────────────────────────────────────────
@router.get("/captions")
def get_marketing_captions(
    film_title:    str  = Query(...),
    genre:         str  = Query("Action"),
    language:      str  = Query("Hindi"),
    release_month: int  = Query(11, ge=1, le=12),
    company:       str  = Query("FilmPulse Productions"),
    handle:        str  = Query("filmpulse"),
    platforms:     str  = Query("instagram,twitter,youtube,facebook,whatsapp",
                               description="Comma-separated platforms"),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    AI-generated marketing captions tailored per platform.
    Each platform gets 2 caption variants for variety.
    """
    platform_list = [p.strip().lower() for p in platforms.split(",") if p.strip()]
    captions = generate_marketing_captions(
        film_title=film_title, genre=genre, language=language,
        release_month=release_month, company=company, handle=handle,
        platforms=platform_list,
    )
    platform_tips = {
        "instagram": "Post at 8–10pm IST. Use Stories + Reels. Tag cast.",
        "twitter":   "Tweet at 12pm + 8pm IST. Add GIF variant. Engage replies.",
        "youtube":   "Post at 5pm. Pin top comment. Add cards at 0:30.",
        "facebook":  "Boost post ₹500/day to 18-35 age group. Add ticket link.",
        "whatsapp":  "Broadcast to film club groups. Keep under 200 chars.",
    }
    return {
        "film_title":    film_title,
        "genre":         genre,
        "language":      language,
        "captions":      captions,
        "platform_tips": {p: platform_tips.get(p, "") for p in platform_list},
    }


# ── 3. A/B Test Caption Pair ─────────────────────────────────────────────────
@router.get("/captions/ab-test")
def get_ab_test_captions(
    film_title: str = Query(...),
    genre:      str = Query("Drama"),
    language:   str = Query("Hindi"),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Generate an A/B test pair: emotional (variant A) vs bold-action (variant B).
    Includes expected engagement prediction per variant.
    """
    return generate_ab_test_captions(film_title, genre, language)


# ── 4. Competitor Comparison ──────────────────────────────────────────────────
@router.get("/competitors")
def competitor_analysis(
    film_title:            str   = Query(...),
    genre:                 str   = Query("Action"),
    budget_cr:             float = Query(80, description="Budget in crores"),
    language:              str   = Query("Hindi"),
    cast_popularity:       float = Query(7.5),
    discoverability_score: float = Query(70),
    hype_score:            float = Query(65),
    platform:              str   = Query("Theatre"),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Compare this film against 30 historical Bollywood films (2019–2024).
    Returns: 5 most similar films, genre benchmarks, market position, revenue projection.
    No auth required — useful for demo.
    """
    return run_competitor_analysis(
        film_title=film_title, genre=genre, budget_cr=budget_cr,
        language=language, cast_popularity=cast_popularity,
        discoverability_score=discoverability_score,
        hype_score=hype_score, platform=platform,
    )


# ── 5. Regional Heatmap ───────────────────────────────────────────────────────
@router.get("/heatmap")
def regional_heatmap(
    film_title:      str   = Query(...),
    genre:           str   = Query("Action"),
    language:        str   = Query("Hindi"),
    budget_cr:       float = Query(80),
    cast_popularity: float = Query(7.5),
    discoverability: float = Query(70),
    release_month:   int   = Query(11, ge=1, le=12),
    top_states:      int   = Query(10, ge=1, le=35),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    State-level audience reach heatmap for all 35 Indian states & UTs.
    Returns GeoJSON-compatible data with lat/lon coordinates and intensity labels.
    Factors: genre affinity, language penetration, screen density, festival timing.
    """
    return generate_regional_heatmap(
        film_title=film_title, genre=genre, language=language,
        budget_cr=budget_cr, cast_popularity=cast_popularity,
        discoverability=discoverability, release_month=release_month,
        top_states=top_states,
    )


# ── 6. Festival Success Probability ──────────────────────────────────────────
@router.get("/festival-score")
def festival_score(
    genre:           str   = Query("Drama"),
    budget_cr:       float = Query(25),
    language:        str   = Query("Hindi"),
    release_month:   int   = Query(10, ge=1, le=12),
    director_films:  int   = Query(1, ge=0, le=20, description="Number of films director has made"),
    subject_novelty: float = Query(0.7, ge=0.0, le=1.0),
    critical_tone:   float = Query(0.7, ge=0.0, le=1.0),
    platform:        str   = Query("Theatre"),
    festivals:       str   = Query("", description="Comma-separated festival IDs, or empty for all"),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Score a film's probability of selection at 9 film festivals (Cannes, TIFF,
    Venice, Berlin, Sundance, BIFF, MAMI, IFFK, IFFI).

    Returns: selection_probability, win_probability, commercial_boost per festival.
    """
    fest_filter = [f.strip() for f in festivals.split(",") if f.strip()] or None
    return score_festival_probability(
        genre=genre, budget_cr=budget_cr, language=language,
        release_month=release_month, director_films=director_films,
        subject_novelty=subject_novelty, critical_tone=critical_tone,
        platform=platform, festivals=fest_filter,
    )


# ── 7. Full Market Intelligence Report ───────────────────────────────────────
@router.get("/market-intelligence")
def market_intelligence(
    film_id:         Optional[int] = Query(None, description="Internal Film ID to autofill data"),
    film_title:      Optional[str] = Query(None),
    genre:           str   = Query("Action"),
    language:        str   = Query("Hindi"),
    budget_cr:       float = Query(80),
    cast_popularity: float = Query(7.5),
    release_month:   int   = Query(11, ge=1, le=12),
    director_films:  int   = Query(2),
    subject_novelty: float = Query(0.6),
    critical_tone:   float = Query(0.7),
    platform:        str   = Query("Theatre"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_producer_or_admin),
):
    """
    [PRODUCER / ADMIN] Compound AI intelligence report combining all 5 engines.
    If film_id is provided, metadata is fetched from the database.
    """
    # 1. Autofill from DB if ID exists
    if film_id:
        film = db.query(Film).filter(Film.id == film_id).first()
        if film:
            film_title = film.title
            genre = film.genre or genre
            language = film.language or language
            budget_cr = film.budget / 10000000 if film.budget else budget_cr  # simple INR -> Cr
            cast_popularity = film.cast_popularity or cast_popularity
            platform = film.platform or platform
            # month extraction (naive)
            if film.release_date and "-" in film.release_date:
                try:
                    release_month = int(film.release_date.split("-")[1])
                except: pass

    if not film_title:
        film_title = "Untitled Project"

    # Run all 5 engines
    competitors = run_competitor_analysis(
        film_title=film_title, genre=genre, budget_cr=budget_cr,
        language=language, cast_popularity=cast_popularity,
        platform=platform,
    )
    heatmap = generate_regional_heatmap(
        film_title=film_title, genre=genre, language=language,
        budget_cr=budget_cr, cast_popularity=cast_popularity,
        release_month=release_month,
    )
    festival = score_festival_probability(
        genre=genre, budget_cr=budget_cr, language=language,
        release_month=release_month, director_films=director_films,
        subject_novelty=subject_novelty, critical_tone=critical_tone,
        platform=platform,
    )
    taglines  = generate_taglines(film_title, genre, release_month)
    captions  = generate_marketing_captions(
        film_title=film_title, genre=genre, language=language,
        release_month=release_month, platforms=["instagram", "twitter"],
    )

    # Distill key insights
    best_tagline_tone = next(iter(taglines))
    best_tagline      = taglines[best_tagline_tone][0] if taglines[best_tagline_tone] else ""

    return {
        "film_title":    film_title,
        "generated_by":  current_user.email,
        "report_sections": {
            "competitive_position": {
                "market_position":    competitors["market_position"],
                "comparable_films":   competitors["comparable_films"][:3],
                "projection_revenue_cr": competitors["revenue_projection"]["projected_cr"],
                "strategy_tips":      competitors["recommendations"][:2],
            },
            "regional_reach": {
                "total_reach_score": heatmap["total_reach_score"],
                "primary_markets":   heatmap["primary_markets"],
                "best_zone":         heatmap["best_zone"],
                "top_5_states":      [
                    {"state": s["state_name"], "score": s["score"], "intensity": s["intensity"]}
                    for s in heatmap["top_states"][:5]
                ],
            },
            "festival_opportunity": {
                "any_festival_probability": festival["summary"]["any_festival_probability"],
                "best_festival":            festival["summary"]["best_festival"],
                "best_selection_prob":      festival["summary"]["best_selection_prob"],
                "top_3_festivals":          festival["festivals"][:3],
                "overall_strategy":         festival["summary"]["recommended_strategy"],
            },
            "creative_assets": {
                "best_poster_tagline":  best_tagline,
                "tagline_tone":         best_tagline_tone,
                "instagram_caption":    captions.get("instagram", [""])[0],
                "twitter_caption":      captions.get("twitter", [""])[0],
                "hashtag_tip":          "Use top 8 hashtags in first comment (Instagram) or inline (Twitter).",
            },
        },
        "executive_summary": (
            f"{film_title} is positioned as a {competitors['market_position'].split('—')[0].strip()} "
            f"with strongest audience reach in {heatmap['best_zone']} India. "
            f"Festival opportunity: {festival['summary']['any_festival_probability']} chance at top 3. "
            f"Recommended release: Month {release_month}."
        ),
    }
