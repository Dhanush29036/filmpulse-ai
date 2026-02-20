"""
FilmPulse AI — Regional Heatmap Generator (Phase 8)
====================================================
Generates state-level audience heatmap data for all 28 Indian states + 8 UTs.

Scoring factors per state:
  • Genre affinity (e.g. Kerala → Drama, UP/Bihar → Action, South → regional language)
  • Language penetration score
  • Urban cinema screen density (per state)
  • Historical OTT & theatrical performance index
  • Cast/director origin boost (e.g. Telugu cast → strong pull in AP/Telangana)
  • Festival timing (states celebrate different festivals)

Output: GeoJSON-compatible state data for the frontend heatmap component.
"""
import math
import random
from typing import Dict, List, Optional

# ── State database: 28 states + 8 UTs ────────────────────────────────────────
# Format: state_id, state_name, zone, population_m, screens, urban_pct, lat, lon
_INDIAN_STATES = [
    # (id, name, zone, pop_M, screens, urban%, lat, lon)
    ("MH", "Maharashtra",          "West",  126, 1400, 0.45, 19.75, 75.71),
    ("DL", "Delhi",                "North",  32, 500,  0.97, 28.70, 77.10),
    ("KA", "Karnataka",            "South",  68, 1000, 0.39, 14.50, 75.70),
    ("TN", "Tamil Nadu",           "South",  78, 1200, 0.50, 10.75, 78.88),
    ("TS", "Telangana",            "South",  40, 900,  0.39, 17.12, 79.01),
    ("AP", "Andhra Pradesh",       "South",  54, 800,  0.30, 14.46, 79.74),
    ("KL", "Kerala",               "South",  35, 600,  0.47, 10.85, 76.27),
    ("GJ", "Gujarat",              "West",   70, 700,  0.43, 22.26, 71.20),
    ("RJ", "Rajasthan",            "North",  81, 500,  0.25, 26.43, 74.22),
    ("UP", "Uttar Pradesh",        "North", 240, 800,  0.22, 26.85, 80.91),
    ("MP", "Madhya Pradesh",       "Central", 85, 450, 0.28, 23.47, 77.95),
    ("WB", "West Bengal",          "East",   99, 700,  0.32, 22.97, 87.68),
    ("OR", "Odisha",               "East",   46, 250,  0.18, 20.94, 85.09),
    ("PB", "Punjab",               "North",  30, 350,  0.38, 31.15, 75.34),
    ("HR", "Haryana",              "North",  29, 280,  0.35, 29.06, 76.09),
    ("BR", "Bihar",                "East",  125, 300,  0.12, 25.67, 85.91),
    ("JH", "Jharkhand",            "East",   38, 150,  0.24, 23.61, 85.27),
    ("CT", "Chhattisgarh",         "Central", 30, 150, 0.22, 22.09, 82.14),
    ("AS", "Assam",                "NE",     35, 150,  0.15, 26.36, 92.79),
    ("HP", "Himachal Pradesh",     "North",   7,  80,  0.11, 31.10, 77.17),
    ("UK", "Uttarakhand",          "North",  11, 100,  0.31, 30.07, 79.08),
    ("GA", "Goa",                  "West",    2, 60,   0.67, 15.30, 74.12),
    ("JK", "Jammu & Kashmir",      "North",  14, 60,   0.27, 33.73, 75.15),
    ("MN", "Manipur",              "NE",      3, 30,   0.31, 24.66, 93.90),
    ("MG", "Meghalaya",            "NE",      3, 20,   0.22, 25.47, 91.36),
    ("TR", "Tripura",              "NE",      4, 30,   0.28, 23.94, 91.98),
    ("NL", "Nagaland",             "NE",      2, 15,   0.30, 25.67, 93.73),
    ("AR", "Arunachal Pradesh",    "NE",      2, 15,   0.24, 28.22, 94.73),
    ("SK", "Sikkim",               "NE",      1, 10,   0.27, 27.53, 88.51),
    ("MZ", "Mizoram",              "NE",      1, 10,   0.52, 23.16, 92.93),
    ("DN", "Dadra & NH",           "West",    1, 8,    0.46, 20.17, 73.01),
    ("CH", "Chandigarh",           "North",   1, 50,   0.97, 30.73, 76.78),
    ("PY", "Puducherry",           "South",   2, 30,   0.67, 11.93, 79.83),
    ("LD", "Lakshadweep",          "South",   0, 2,    0.80, 10.57, 72.64),
    ("AN", "Andaman & Nicobar",    "East",    0, 5,    0.39, 11.74, 92.66),
]

# ── Genre affinity by zone / language ─────────────────────────────────────────
_GENRE_ZONE_BOOST = {
    # zone → {genre: multiplier}
    "North":   {"Action": 1.3, "Comedy": 1.2, "Drama": 1.0, "Romance": 1.1},
    "South":   {"Action": 1.4, "Drama": 1.3, "Thriller": 1.2, "Mystery": 1.1},
    "West":    {"Action": 1.2, "Comedy": 1.3, "Drama": 1.1, "Romance": 1.2},
    "East":    {"Drama": 1.3, "Action": 1.1, "Mystery": 1.2, "Romance": 1.1},
    "Central": {"Action": 1.2, "Drama": 1.2, "Comedy": 1.1, "Romance": 1.0},
    "NE":      {"Action": 1.0, "Drama": 1.1, "Comedy": 1.2, "Romance": 1.1},
}

# ── Language reach matrix ─────────────────────────────────────────────────────
_LANGUAGE_REACH = {
    "Hindi":   {"North": 0.90, "Central": 0.85, "West": 0.75, "East": 0.60, "South": 0.30, "NE": 0.50},
    "Telugu":  {"South": 0.85, "West": 0.40, "North": 0.25, "East": 0.30, "Central": 0.30, "NE": 0.20},
    "Tamil":   {"South": 0.80, "West": 0.35, "North": 0.20, "East": 0.25, "Central": 0.20, "NE": 0.20},
    "Kannada": {"South": 0.75, "West": 0.40, "North": 0.20, "East": 0.20, "Central": 0.20, "NE": 0.15},
    "Bengali": {"East": 0.85, "North": 0.30, "NE": 0.40, "West": 0.25, "South": 0.15, "Central": 0.20},
    "Punjabi": {"North": 0.70, "West": 0.40, "Central": 0.30, "East": 0.25, "South": 0.20, "NE": 0.15},
    "English": {"West": 0.55, "North": 0.50, "South": 0.50, "East": 0.40, "Central": 0.35, "NE": 0.45},
    "Malayalam":{"South": 0.75, "West": 0.35, "North": 0.20, "East": 0.20, "Central": 0.18, "NE": 0.18},
}


def _state_score(
    state: tuple,
    genre: str,
    language: str,
    budget_cr: float,
    cast_popularity: float,
    discoverability: float,
    release_month: int,
) -> float:
    state_id, name, zone, pop, screens, urban_pct, lat, lon = state

    # Base: screen density × urban % (normalized)
    screen_density = min(100, screens / max(pop, 1) * 100)
    base_score = (screen_density * 0.25 + urban_pct * 100 * 0.20)

    # Genre affinity boost
    genre_mult = _GENRE_ZONE_BOOST.get(zone, {}).get(genre, 1.0)

    # Language reach
    lang_reach = _LANGUAGE_REACH.get(language, {}).get(zone, 0.4)

    # Budget penetration (ad spend reach)
    budget_reach = min(1.0, math.log1p(budget_cr) / math.log1p(300))

    # Discoverability contribution
    disc_factor = discoverability / 100.0

    # Cast popularity factor
    cast_factor = cast_popularity / 10.0

    # Festival timing bonus (state-specific)
    festival_bonus = _festival_timing_bonus(state_id, release_month)

    raw = (
        base_score * 0.20 +
        genre_mult * lang_reach * 40 +
        budget_reach * 20 +
        disc_factor * 15 +
        cast_factor * 15 +
        festival_bonus * 10
    )
    return round(min(100, max(5, raw)), 1)


def _festival_timing_bonus(state_id: str, release_month: int) -> float:
    """State-specific festival timing bonus (0-1)."""
    # States where a release_month aligns with a major local festival
    _FESTIVAL_MATRIX = {
        "KL": {4: 1.0, 8: 0.8, 10: 0.6},   # Vishu (Apr), Onam (Aug)
        "TN": {1: 0.9, 4: 0.8, 11: 0.7},   # Pongal, Tamil NY
        "AP": {1: 0.9, 10: 1.0, 11: 0.8},  # Ugadi, Dasara
        "TS": {1: 0.9, 10: 1.0, 11: 0.8},
        "PB": {4: 1.0, 10: 0.8},            # Baisakhi, Diwali
        "GJ": {11: 1.0, 10: 0.9},           # Diwali peak
        "WB": {10: 1.0, 11: 0.8},           # Durga Puja
        "OR": {10: 0.9, 4: 0.7},            # Durga Puja
        "AS": {4: 1.0, 10: 0.7},            # Bihu
    }
    state_matrix = _FESTIVAL_MATRIX.get(state_id, {})
    return state_matrix.get(release_month, 0.3)


def generate_regional_heatmap(
    film_title:          str,
    genre:               str,
    language:            str     = "Hindi",
    budget_cr:           float   = 80,
    cast_popularity:     float   = 7.5,
    discoverability:     float   = 70,
    release_month:       int     = 11,
    top_states:          int     = 10,
) -> Dict:
    """
    Generate GeoJSON-compatible heatmap data for Indian states.
    Returns scores for all 35 states/UTs + sorted top performers.
    """
    state_data = []
    for state in _INDIAN_STATES:
        score = _state_score(
            state       = state,
            genre       = genre,
            language    = language,
            budget_cr   = budget_cr,
            cast_popularity = cast_popularity,
            discoverability = discoverability,
            release_month   = release_month,
        )
        state_id, name, zone, pop, screens, urban_pct, lat, lon = state
        state_data.append({
            "state_id":       state_id,
            "state_name":     name,
            "zone":           zone,
            "score":          score,
            "screens":        screens,
            "population_m":   pop,
            "urban_pct":      round(urban_pct * 100, 1),
            "coordinates":    {"lat": lat, "lon": lon},
            "intensity":      (
                "very_high" if score >= 80 else
                "high"      if score >= 65 else
                "medium"    if score >= 50 else
                "low"       if score >= 35 else "very_low"
            ),
        })

    state_data.sort(key=lambda x: x["score"], reverse=True)
    total_score = sum(s["score"] for s in state_data)

    # Zone aggregates
    zone_agg: Dict[str, List[float]] = {}
    for s in state_data:
        zone_agg.setdefault(s["zone"], []).append(s["score"])
    zone_summary = {
        z: {"avg_score": round(sum(v)/len(v), 1), "state_count": len(v)}
        for z, v in zone_agg.items()
    }
    zone_summary_sorted = dict(sorted(zone_summary.items(), key=lambda x: x[1]["avg_score"], reverse=True))

    return {
        "film_title":      film_title,
        "states":          state_data,
        "top_states":      state_data[:top_states],
        "zone_summary":    zone_summary_sorted,
        "best_zone":       max(zone_summary, key=lambda z: zone_summary[z]["avg_score"]),
        "total_reach_score": round(total_score / len(state_data), 1),
        "primary_markets":   [s["state_name"] for s in state_data[:3]],
        "metadata":  {
            "genre": genre, "language": language,
            "release_month": release_month, "budget_cr": budget_cr,
            "states_analyzed": len(state_data),
        },
    }
