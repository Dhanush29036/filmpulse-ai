"""
FilmPulse AI — Discoverability Score (Phase 3 Upgrade)
=======================================================
Signature FilmPulse formula:

  Discoverability Score =
    (0.25 × Audience Match)
  + (0.20 × Buzz Score)
  + (0.15 × Competition Index)
  + (0.20 × Budget Efficiency)
  + (0.20 × Release Timing Score)

All sub-scores normalised to [0,1]. Final output in [0,100].

New in Phase 3:
  • auto_compute() — derive all sub-scores from raw inputs (no manual normalization)
  • Release timing model using month-based festival calendar
  • Budget efficiency benchmarks by genre
  • Competition index from release_date slot
"""

import math
from typing import Optional

# ── Genre Revenue Benchmarks (INR) ───────────────────────────────────────────
GENRE_BUDGET_BENCHMARKS = {
    "Action":   {"p25": 3e7,  "p75": 1.5e8},
    "Romance":  {"p25": 1e7,  "p75": 6e7 },
    "Thriller": {"p25": 1.5e7,"p75": 8e7 },
    "Comedy":   {"p25": 1e7,  "p75": 5e7 },
    "Drama":    {"p25": 8e6,  "p75": 4e7 },
    "Horror":   {"p25": 5e6,  "p75": 3e7 },
}

# ── Festive/Premium Release Windows (month → timing quality 0-1) ──────────────
RELEASE_TIMING_SCORES = {
    1:  0.80,   # Jan — Republic Day
    2:  0.65,   # Feb — Valentine's Day boost
    3:  0.70,   # Mar — Holi
    4:  0.60,   # Apr — IPL competition
    5:  0.55,   # May — summer, competitive
    6:  0.65,   # Jun — Eid window
    7:  0.70,   # Jul — post-Eid, schools resume
    8:  0.58,   # Aug — monsoon, lower footfall
    9:  0.62,   # Sep — moderate
    10: 0.85,   # Oct — Navratri / Durga Puja
    11: 0.88,   # Nov — Diwali ⭐ best window
    12: 0.82,   # Dec — Christmas + New Year
}

# ── Competition Crowding Index (hardcoded approximation) ─────────────────────
# Lower crowding → Higher competition index passed to formula
MONTHLY_CROWDING = {
    1: 0.7, 2: 0.6, 3: 0.65, 4: 0.5, 5: 0.55,
    6: 0.72, 7: 0.68, 8: 0.6, 9: 0.65,
    10: 0.55, 11: 0.45, 12: 0.5,
}


# ══════════════════════════════════════════════════════════════════════════════
# Core Formula
# ══════════════════════════════════════════════════════════════════════════════
def compute_discoverability_score(
    audience_match: float,
    buzz_score: float,
    competition_index: float,
    budget_efficiency: float,
    release_timing: float,
) -> dict:
    """
    Compute FilmPulse Discoverability Score from 5 pre-normalised sub-scores.

    Args (all in [0,1]):
        audience_match:    Genre/language/demographic fit
        buzz_score:        Social media / trailer hype
        competition_index: Market space (1 = least competition)
        budget_efficiency: Budget vs. genre benchmark
        release_timing:    Release window quality

    Returns full dict with score, grade, interpretation, and breakdown.
    """
    am = max(0.0, min(1.0, audience_match))
    bz = max(0.0, min(1.0, buzz_score))
    ci = max(0.0, min(1.0, competition_index))
    be = max(0.0, min(1.0, budget_efficiency))
    rt = max(0.0, min(1.0, release_timing))

    raw   = (0.25 * am) + (0.20 * bz) + (0.15 * ci) + (0.20 * be) + (0.20 * rt)
    score = round(raw * 100, 1)

    return {
        "score": score,
        "grade": _grade(score),
        "interpretation": _interpret(score),
        "breakdown": {
            "audience_match":    {"weight": "25%", "raw": round(am, 3), "weighted": round(0.25 * am * 100, 1)},
            "buzz_score":        {"weight": "20%", "raw": round(bz, 3), "weighted": round(0.20 * bz * 100, 1)},
            "competition_index": {"weight": "15%", "raw": round(ci, 3), "weighted": round(0.15 * ci * 100, 1)},
            "budget_efficiency": {"weight": "20%", "raw": round(be, 3), "weighted": round(0.20 * be * 100, 1)},
            "release_timing":    {"weight": "20%", "raw": round(rt, 3), "weighted": round(0.20 * rt * 100, 1)},
        },
        "formula": "0.25×AudienceMatch + 0.20×Buzz + 0.15×Competition + 0.20×BudgetEfficiency + 0.20×ReleaseTiming",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Auto-Compute from Raw Inputs (Phase 3 new)
# ══════════════════════════════════════════════════════════════════════════════
def auto_compute_discoverability(
    genre: str,
    budget: float,
    language: str,
    cast_popularity: float,
    trailer_sentiment: float,
    release_month: int,
    hype_score: Optional[float] = None,
    genre_score: Optional[float] = None,
) -> dict:
    """
    Derive all 5 Discoverability sub-scores from raw film parameters.
    No manual normalisation required.

    Args:
        genre:             Film genre string
        budget:            Production budget (INR)
        language:          Release language
        cast_popularity:   Star cast rating (1-10)
        trailer_sentiment: Trailer sentiment score (0-1)
        release_month:     Integer 1-12
        hype_score:        Optional pre-computed hype score (0-100)
        genre_score:       Optional GBR revenue multiplier normalised score (0-1)
    """
    release_month = max(1, min(12, int(release_month)))

    # ── 1. Audience Match ────────────────────────────────────────────────────
    lang_reach = {
        "Hindi": 0.88, "English": 0.72, "Tamil": 0.65,
        "Telugu": 0.67, "Bengali": 0.55, "Marathi": 0.50,
    }
    gs    = genre_score if genre_score is not None else 0.65
    lr    = lang_reach.get(language, 0.70)
    cp_n  = min(1.0, max(0.0, (cast_popularity - 1) / 9.0))  # normalise 1-10 → 0-1
    am    = 0.40 * gs + 0.35 * lr + 0.25 * cp_n

    # ── 2. Buzz Score ────────────────────────────────────────────────────────
    ts_n = max(0.0, min(1.0, trailer_sentiment))
    if hype_score is not None:
        bz = 0.55 * (hype_score / 100.0) + 0.45 * ts_n
    else:
        bz = ts_n

    # ── 3. Competition Index ─────────────────────────────────────────────────
    # Lower crowding → more discoverable
    crowding = MONTHLY_CROWDING.get(release_month, 0.6)
    ci = 1.0 - crowding   # invert: less crowded = higher score

    # ── 4. Budget Efficiency ─────────────────────────────────────────────────
    bench = GENRE_BUDGET_BENCHMARKS.get(genre, {"p25": 1e7, "p75": 8e7})
    p25, p75 = bench["p25"], bench["p75"]
    if budget < p25:
        # Under-funded relative to genre
        be = max(0.1, 0.3 * (budget / p25))
    elif budget <= p75:
        # Sweet spot — linear 0.5-0.95
        be = 0.5 + 0.45 * (budget - p25) / (p75 - p25)
    else:
        # Over budget — diminishing returns
        be = min(1.0, 0.95 + 0.05 * math.log1p((budget - p75) / p75))

    # ── 5. Release Timing ────────────────────────────────────────────────────
    rt = RELEASE_TIMING_SCORES.get(release_month, 0.65)

    result = compute_discoverability_score(am, bz, ci, be, rt)
    result["sub_score_inputs"] = {
        "audience_match":    round(am, 3),
        "buzz_score":        round(bz, 3),
        "competition_index": round(ci, 3),
        "budget_efficiency": round(be, 3),
        "release_timing":    round(rt, 3),
    }
    result["release_window"] = _release_window_label(release_month)
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────
def _grade(score: float) -> str:
    if   score >= 82: return "A+"
    elif score >= 75: return "A"
    elif score >= 65: return "B"
    elif score >= 50: return "C"
    else:             return "D"

def _interpret(score: float) -> str:
    if   score >= 82: return "Outstanding discoverability — prime wide theatrical release. 🔥"
    elif score >= 75: return "Excellent discoverability — strong OTT + theatrical combo. ✨"
    elif score >= 65: return "Good discoverability — selective theatrical + OTT premiere. 👍"
    elif score >= 50: return "Moderate discoverability — niche audiences and festival circuit. 🤔"
    else:             return "Low discoverability — rethink positioning before release. ⚠️"

def _release_window_label(month: int) -> str:
    windows = {
        1: "Republic Day Weekend", 2: "Valentine's Day Window",
        3: "Holi Release", 6: "Eid Window", 10: "Navratri / Durga Puja",
        11: "Diwali ⭐ (Peak Window)", 12: "Christmas / New Year",
    }
    return windows.get(month, f"Month {month}")
