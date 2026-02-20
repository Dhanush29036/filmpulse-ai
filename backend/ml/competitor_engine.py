"""
FilmPulse AI — Competitor Comparison Engine (Phase 8)
======================================================
Compares an upcoming film against:
  • Historical box office dataset (30 reference films, Bollywood 2019–2024)
  • Genre-level performance benchmarks
  • Budget tier analysis
  • Cast & director strength comparison

Outputs:
  • Market position (Top 10% / Mid-tier / Underperformer projection)
  • Competitive score vs 3 nearest comparable films
  • Revenue gap analysis
  • Strategic recommendations
"""
import math
import random
from typing import List, Dict, Optional, Tuple

# ── Historical reference dataset (2019–2024 Bollywood + regional) ─────────────
# Format: title, genre, budget_cr, box_office_cr, language, cast_power (1-10), platform
_REFERENCE_FILMS = [
    # Title,                Genre,     Budget, BO,   Lang,     Cast, Platform
    ("KGF Chapter 2",       "Action",  100,   1200, "Kannada", 9.5, "Theatre"),
    ("Pathaan",             "Action",  250,   1050, "Hindi",   9.8, "Theatre"),
    ("Jawan",               "Action",  300,   1160, "Hindi",   9.9, "Theatre"),
    ("Animal",              "Action",  200,    900, "Hindi",   9.2, "Theatre"),
    ("Dunki",               "Drama",   200,    470, "Hindi",   9.8, "Theatre"),
    ("Fighter",             "Action",  250,    250, "Hindi",   9.0, "Theatre"),
    ("12th Fail",           "Drama",    25,    130, "Hindi",   7.5, "Theatre"),
    ("Piku",                "Drama",    25,     80, "Hindi",   9.0, "Both"),
    ("RRR",                 "Action",  550,   1200, "Telugu",  9.5, "Theatre"),
    ("Bahubali 2",          "Action",  250,   1810, "Telugu",  8.8, "Theatre"),
    ("Kantara",             "Drama",    16,    400, "Kannada", 8.5, "Theatre"),
    ("Vikram",              "Thriller", 175,   500, "Tamil",   9.0, "Theatre"),
    ("Leo",                 "Action",  200,    620, "Tamil",   9.5, "Theatre"),
    ("2.0",                 "Action",  600,    660, "Tamil",   9.8, "Both"),
    ("Pushpa",              "Action",   30,    373, "Telugu",  9.0, "Theatre"),
    ("Pushpa 2",            "Action",  200,   1800, "Telugu",  9.2, "Theatre"),
    ("Laapataa Ladies",     "Comedy",   20,    65,  "Hindi",   7.0, "OTT"),
    ("Crew",                "Comedy",   45,    70,  "Hindi",   8.5, "Theatre"),
    ("Article 370",         "Thriller", 50,   150, "Hindi",   8.5, "Theatre"),
    ("Merry Christmas",     "Thriller", 80,    35, "Hindi",   9.0, "Theatre"),
    ("Sam Bahadur",         "Drama",    70,   175, "Hindi",   8.8, "Theatre"),
    ("Ganapath",            "Action",  100,    10, "Hindi",   7.5, "Theatre"),
    ("Gadar 2",             "Action",   60,   687, "Hindi",   8.0, "Theatre"),
    ("OMG 2",               "Drama",    40,   200, "Hindi",   9.0, "Theatre"),
    ("Dream Girl 2",        "Comedy",   40,   260, "Hindi",   8.5, "Theatre"),
    ("Jogi",                "Drama",    30,    25, "Hindi",   7.5, "OTT"),
    ("Mission Raniganj",    "Drama",    80,    35, "Hindi",   9.0, "Theatre"),
    ("Tu Jhoothi Main Makkaar","Romance",80,  185, "Hindi",   8.5, "Theatre"),
    ("Rocky Aur Rani",      "Drama",   150,   185, "Hindi",   9.5, "Theatre"),
    ("Adipurush",           "Action",  500,   395, "Hindi",   7.5, "Theatre"),
]


def _compute_roi(budget: float, box_office: float) -> float:
    return round((box_office - budget) / budget * 100, 1) if budget > 0 else 0


def _similarity_score(ref: tuple, target_genre: str, target_budget: float,
                       target_cast: float, target_lang: str) -> float:
    """Compute cosine-like similarity between a reference film and a target."""
    _, r_genre, r_budget, _, r_lang, r_cast, _ = ref
    genre_match   = 1.0 if r_genre == target_genre else 0.3
    budget_ratio  = min(r_budget, target_budget) / max(r_budget, target_budget, 1)
    cast_diff     = 1.0 - abs(r_cast - target_cast) / 10.0
    lang_match    = 1.0 if r_lang == target_lang else 0.5
    return round(genre_match * 0.35 + budget_ratio * 0.30 + cast_diff * 0.20 + lang_match * 0.15, 3)


def find_comparable_films(
    genre: str,
    budget_cr: float,             # budget in crores
    cast_popularity: float,       # 1-10
    language: str = "Hindi",
    top_n: int = 5,
) -> List[Dict]:
    """Find the most similar historical films to compare against."""
    scored = []
    for film in _REFERENCE_FILMS:
        sim = _similarity_score(film, genre, budget_cr, cast_popularity, language)
        scored.append((sim, film))
    scored.sort(key=lambda x: x[0], reverse=True)
    result = []
    for sim, film in scored[:top_n]:
        title, g, bgt, bo, lang, cast, plat = film
        result.append({
            "title":          title,
            "genre":          g,
            "budget_cr":      bgt,
            "box_office_cr":  bo,
            "language":       lang,
            "cast_power":     cast,
            "platform":       plat,
            "roi_pct":        _compute_roi(bgt, bo),
            "similarity":     sim,
            "multiplier":     round(bo / bgt, 2),
        })
    return result


def compute_market_position(
    genre: str,
    budget_cr: float,
    cast_popularity: float,
    language: str = "Hindi",
    discoverability_score: float = 70,
    hype_score: float = 65,
) -> str:
    """Estimate market position tier."""
    genre_benchmarks = {
        "Action": 85, "Thriller": 70, "Drama": 60,
        "Comedy": 55, "Romance": 55, "Mystery": 65, "Horror": 50,
    }
    bench = genre_benchmarks.get(genre, 65)
    composite = (
        discoverability_score * 0.30 +
        hype_score * 0.25 +
        min(100, cast_popularity * 10) * 0.25 +
        min(100, math.log1p(budget_cr) / math.log1p(600) * 100) * 0.20
    )
    if composite >= bench + 15:
        return "Top 10% — Blockbuster territory"
    elif composite >= bench:
        return "Upper Mid-Tier — Strong commercial potential"
    elif composite >= bench - 15:
        return "Mid-Tier — Steady performer projection"
    else:
        return "Lower Tier — OTT-first strategy recommended"


def run_competitor_analysis(
    film_title: str,
    genre: str,
    budget_cr: float,
    language: str = "Hindi",
    cast_popularity: float = 7.5,
    discoverability_score: float = 70,
    hype_score: float = 65,
    platform: str = "Theatre",
) -> Dict:
    """
    Full competitor comparison:
    - 5 most similar historical films
    - Genre benchmarks (avg budget, avg BO, ROI range)
    - Market position
    - Revenue gap vs best comparable
    - Strategic recommendations
    """
    comparables = find_comparable_films(genre, budget_cr, cast_popularity, language, top_n=5)
    position    = compute_market_position(
        genre, budget_cr, cast_popularity, language, discoverability_score, hype_score
    )

    # Genre-level benchmarks
    genre_films  = [f for f in _REFERENCE_FILMS if f[1] == genre]
    avg_budget   = sum(f[2] for f in genre_films) / max(len(genre_films), 1)
    avg_bo       = sum(f[3] for f in genre_films) / max(len(genre_films), 1)
    avg_mult     = round(avg_bo / avg_budget, 2) if avg_budget else 2.0
    max_bo       = max((f[3] for f in genre_films), default=0)
    median_roi   = sorted([_compute_roi(f[2], f[3]) for f in genre_films])
    med_roi      = median_roi[len(median_roi) // 2] if median_roi else 100

    # Best comparable (highest similarity × multiplier)
    best_comp    = comparables[0] if comparables else {}
    revenue_gap  = 0
    if best_comp:
        projected = budget_cr * best_comp["multiplier"]
        revenue_gap = round(projected - budget_cr, 1)

    # Recommendations
    recs = []
    if cast_popularity < 7.5:
        recs.append("Boost cast visibility via reality show appearances and OTT cameos.")
    if budget_cr < avg_budget * 0.5:
        recs.append(f"Budget is 50%+ below {genre} genre average (₹{avg_budget:.0f} Cr). Consider platform-first strategy.")
    if discoverability_score < 65:
        recs.append("Increase pre-release buzz via digital campaigns 8+ weeks before release.")
    if platform == "Theatre" and genre in ("Drama", "Mystery") and budget_cr < 50:
        recs.append("Low-budget Drama/Mystery films outperform on OTT — consider hybrid release.")
    if comparables and comparables[0]["multiplier"] > 5:
        recs.append(f"Films similar to '{comparables[0]['title']}' achieved {comparables[0]['multiplier']}× ROI — strong upside if marketed correctly.")
    if not recs:
        recs.append("Strong positioning — maintain momentum with consistent social media engagement.")

    return {
        "film_title":         film_title,
        "market_position":    position,
        "comparable_films":   comparables,
        "genre_benchmarks":   {
            "genre":           genre,
            "avg_budget_cr":   round(avg_budget, 1),
            "avg_box_office":  round(avg_bo, 1),
            "avg_multiplier":  avg_mult,
            "genre_roi_median": med_roi,
            "genre_peak_bo":   max_bo,
            "films_analyzed":  len(genre_films),
        },
        "revenue_projection": {
            "based_on":    comparables[0]["title"] if comparables else "N/A",
            "multiplier":  comparables[0]["multiplier"] if comparables else 2.0,
            "projected_cr": round(budget_cr * (comparables[0]["multiplier"] if comparables else 2), 1),
            "revenue_gap_cr": revenue_gap,
        },
        "recommendations": recs,
    }
