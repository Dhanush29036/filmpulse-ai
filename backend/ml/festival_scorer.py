"""
FilmPulse AI — Festival Success Probability Scorer (Phase 8)
============================================================
Scores a film's probability of:
  1. Being selected for film festivals (jury/competition)
  2. Winning awards at each festival
  3. Benefiting commercially from festival screenings

Festivals covered:
  International: Cannes, TIFF, Venice, Berlin, Sundance, BIFF (Busan)
  Indian: MAMI (Mumbai), IFFK (Kerala), IFFI (Goa), BAIFTA, NFAI

Festival selection is based on:
  • Genre fit (art house → Drama/Mystery/Thriller, NOT Action/Comedy blockbusters)
  • Budget tier (festival films typically < ₹50 Cr)
  • Director novelty (first/second film scores higher)
  • Language (regional films have advantage at MAMI, IFFK)
  • Audience sentiment / critical tone
  • Release platform (OTT-first gives festival discovery advantage)
  • Subject matter novelty (social relevance score)
"""
import math
from typing import Dict, List, Optional

# ── Festival definitions ──────────────────────────────────────────────────────
_FESTIVALS = [
    # id, name, tier, location, type, genre_weights, budget_max_cr, best_months
    {
        "id":          "cannes",
        "name":        "Cannes Film Festival",
        "tier":        "A+",
        "location":    "France",
        "type":        "international",
        "genre_fit":   {"Drama": 1.0, "Mystery": 0.9, "Thriller": 0.85, "Romance": 0.7,
                        "Comedy": 0.4, "Action": 0.3, "Horror": 0.5},
        "budget_sweet_spot": (5, 80),   # crores
        "language_bonus":    {"French": 0.2, "Hindi": 0.05, "Tamil": 0.1, "Bengali": 0.15},
        "best_months":       [5],
        "commercial_boost":  1.25,      # box office multiplier if selected
        "prestige_score":    100,
    },
    {
        "id":          "tiff",
        "name":        "Toronto International Film Festival",
        "tier":        "A+",
        "location":    "Canada",
        "type":        "international",
        "genre_fit":   {"Drama": 1.0, "Thriller": 0.9, "Mystery": 0.85, "Comedy": 0.7,
                        "Action": 0.5, "Romance": 0.75, "Horror": 0.6},
        "budget_sweet_spot": (10, 150),
        "language_bonus":    {"English": 0.15, "Hindi": 0.08, "Tamil": 0.1},
        "best_months":       [9],
        "commercial_boost":  1.40,
        "prestige_score":    95,
    },
    {
        "id":          "venice",
        "name":        "Venice Film Festival",
        "tier":        "A+",
        "location":    "Italy",
        "type":        "international",
        "genre_fit":   {"Drama": 1.0, "Mystery": 0.95, "Thriller": 0.9, "Horror": 0.7,
                        "Romance": 0.8, "Comedy": 0.4, "Action": 0.3},
        "budget_sweet_spot": (5, 100),
        "language_bonus":    {"Italian": 0.15, "Hindi": 0.05, "Bengali": 0.15},
        "best_months":       [8, 9],
        "commercial_boost":  1.20,
        "prestige_score":    95,
    },
    {
        "id":          "berlin",
        "name":        "Berlin International Film Festival (Berlinale)",
        "tier":        "A+",
        "location":    "Germany",
        "type":        "international",
        "genre_fit":   {"Drama": 1.0, "Mystery": 0.9, "Thriller": 0.85, "Comedy": 0.7,
                        "Action": 0.4, "Romance": 0.75, "Horror": 0.55},
        "budget_sweet_spot": (5, 100),
        "language_bonus":    {"German": 0.15, "Hindi": 0.06, "Bengali": 0.15},
        "best_months":       [2],
        "commercial_boost":  1.15,
        "prestige_score":    90,
    },
    {
        "id":          "sundance",
        "name":        "Sundance Film Festival",
        "tier":        "A",
        "location":    "USA",
        "type":        "international",
        "genre_fit":   {"Drama": 0.9, "Mystery": 0.9, "Thriller": 0.85, "Comedy": 0.75,
                        "Action": 0.4, "Horror": 0.7, "Romance": 0.7},
        "budget_sweet_spot": (2, 50),
        "language_bonus":    {"English": 0.2, "Hindi": 0.05},
        "best_months":       [1],
        "commercial_boost":  1.35,
        "prestige_score":    85,
    },
    {
        "id":          "biff",
        "name":        "Busan International Film Festival (BIFF)",
        "tier":        "A",
        "location":    "South Korea",
        "type":        "international",
        "genre_fit":   {"Drama": 0.95, "Thriller": 0.95, "Mystery": 0.9, "Action": 0.7,
                        "Comedy": 0.65, "Horror": 0.7, "Romance": 0.75},
        "budget_sweet_spot": (5, 120),
        "language_bonus":    {"Hindi": 0.08, "Tamil": 0.12, "Telugu": 0.1, "Bengali": 0.12},
        "best_months":       [10],
        "commercial_boost":  1.20,
        "prestige_score":    80,
    },
    {
        "id":          "mami",
        "name":        "MAMI Mumbai Film Festival",
        "tier":        "B+",
        "location":    "India",
        "type":        "indian",
        "genre_fit":   {"Drama": 1.0, "Mystery": 0.95, "Thriller": 0.9, "Comedy": 0.75,
                        "Action": 0.55, "Romance": 0.8, "Horror": 0.6},
        "budget_sweet_spot": (1, 60),
        "language_bonus":    {"Hindi": 0.15, "Marathi": 0.2, "Tamil": 0.1, "Bengali": 0.15},
        "best_months":       [10, 11],
        "commercial_boost":  1.15,
        "prestige_score":    70,
    },
    {
        "id":          "iffk",
        "name":        "IFFK Kerala International Film Festival",
        "tier":        "B+",
        "location":    "India",
        "type":        "indian",
        "genre_fit":   {"Drama": 1.0, "Mystery": 1.0, "Thriller": 0.9, "Comedy": 0.65,
                        "Action": 0.4, "Romance": 0.8, "Horror": 0.55},
        "budget_sweet_spot": (1, 40),
        "language_bonus":    {"Malayalam": 0.3, "Tamil": 0.1, "Hindi": 0.08},
        "best_months":       [12],
        "commercial_boost":  1.10,
        "prestige_score":    65,
    },
    {
        "id":          "iffi",
        "name":        "IFFI Goa (International Film Festival of India)",
        "tier":        "B",
        "location":    "India",
        "type":        "indian",
        "genre_fit":   {"Drama": 0.95, "Mystery": 0.9, "Thriller": 0.85, "Comedy": 0.7,
                        "Action": 0.6, "Romance": 0.75, "Horror": 0.6},
        "budget_sweet_spot": (2, 200),
        "language_bonus":    {"Hindi": 0.12, "English": 0.1, "Tamil": 0.1},
        "best_months":       [11],
        "commercial_boost":  1.12,
        "prestige_score":    60,
    },
]


def _budget_fit_score(budget_cr: float, sweet_spot: tuple) -> float:
    lo, hi = sweet_spot
    if lo <= budget_cr <= hi:
        # Peak at midpoint
        mid = (lo + hi) / 2
        return 1.0 - abs(budget_cr - mid) / ((hi - lo) / 2 + 1) * 0.4
    elif budget_cr < lo:
        return max(0.3, budget_cr / lo)
    else:
        return max(0.2, hi / budget_cr)


def score_festival_probability(
    genre:             str,
    budget_cr:         float,
    language:          str   = "Hindi",
    release_month:     int   = 11,
    director_films:    int   = 1,    # how many films has the director made
    subject_novelty:   float = 0.6,  # 0-1 (how unique/social is the subject)
    critical_tone:     float = 0.7,  # 0-1 (from audience/critic sentiment)
    platform:          str   = "Theatre",
    festivals:         Optional[List[str]] = None,
) -> Dict:
    """
    Score a film's probability of selection and success at 9 film festivals.

    Returns list of festival results sorted by selection probability.
    """
    results = []

    # Director novelty: fresh directors score higher at art-house festivals
    director_novelty = 1.0 if director_films <= 2 else max(0.5, 1.0 - (director_films - 2) * 0.08)

    # OTT-platform bonus for discovery
    platform_bonus = 0.10 if platform == "OTT" else 0.0

    for fest in _FESTIVALS:
        if festivals and fest["id"] not in festivals:
            continue

        # 1. Genre fit
        genre_score   = fest["genre_fit"].get(genre, 0.5)

        # 2. Budget fit
        budget_score  = _budget_fit_score(budget_cr, fest["budget_sweet_spot"])

        # 3. Language bonus
        lang_bonus    = fest["language_bonus"].get(language, 0.0)

        # 4. Release month alignment (best_months gives +10%)
        month_bonus   = 0.10 if release_month in fest["best_months"] else 0.0

        # 5. Subject novelty (unique/social subjects = festival catnip)
        novelty_score = subject_novelty

        # 6. Critical tone (good early reviews boost chances)
        crit_score    = critical_tone

        # Weighted composite
        composite = (
            genre_score    * 0.30 +
            budget_score   * 0.20 +
            novelty_score  * 0.15 +
            crit_score     * 0.15 +
            director_novelty * 0.10 +
            lang_bonus +
            month_bonus +
            platform_bonus
        )
        prob = round(min(0.95, max(0.02, composite)), 3)

        # Win probability (conditional on selection)
        win_prob = round(prob * (0.10 + crit_score * 0.20 + novelty_score * 0.15), 3)

        # Commercial impact if selected
        commercial_boost = fest["commercial_boost"]

        results.append({
            "festival_id":         fest["id"],
            "festival_name":       fest["name"],
            "tier":                fest["tier"],
            "location":            fest["location"],
            "type":                fest["type"],
            "selection_probability": prob,
            "selection_pct":       f"{int(prob * 100)}%",
            "win_probability":     win_prob,
            "win_pct":             f"{int(win_prob * 100)}%",
            "commercial_boost":    f"{int((commercial_boost - 1) * 100)}% revenue uplift if selected",
            "prestige_score":      fest["prestige_score"],
            "recommended_months":  fest["best_months"],
            "strategy":            _festival_strategy(prob, fest),
        })

    results.sort(key=lambda x: x["selection_probability"], reverse=True)

    # Best bet
    best = results[0] if results else {}
    top_3_probs = [r["selection_probability"] for r in results[:3]]
    any_festival_prob = round(1 - math.prod(1 - p for p in top_3_probs), 3) if top_3_probs else 0

    return {
        "summary": {
            "best_festival":           best.get("festival_name", "N/A"),
            "best_selection_prob":     best.get("selection_pct", "0%"),
            "any_festival_probability": f"{int(any_festival_prob * 100)}%",
            "total_festivals_scored":  len(results),
            "recommended_strategy":    _overall_strategy(results, genre, budget_cr),
        },
        "festivals": results,
    }


def _festival_strategy(prob: float, fest: Dict) -> str:
    if prob >= 0.70:
        return f"Strong candidate — submit early to {fest['name']}. Prioritise."
    elif prob >= 0.50:
        return f"Good chance — apply with strong press kit & director statement."
    elif prob >= 0.30:
        return f"Moderate chance — position {fest['name']} as a secondary target."
    else:
        return "Low priority for this festival cycle."


def _overall_strategy(results: List[Dict], genre: str, budget_cr: float) -> str:
    top = [r for r in results if r["selection_probability"] >= 0.50]
    if len(top) >= 3:
        return ("Strong festival profile — pursue Cannes/TIFF/MAMI simultaneously. "
                "Festival premiere will amplify theatrical release.")
    elif len(top) >= 1:
        return (f"Focus resources on {top[0]['festival_name']}. "
                "A single major selection is worth 2× marketing spend.")
    elif genre in ("Drama", "Mystery") and budget_cr < 50:
        return ("Classic festival film profile but scores are marginal — "
                "invest in a compelling press kit and director Q&A strategy.")
    else:
        return ("Not optimised for festival circuit. "
                "Better ROI via direct release + digital marketing strategy.")
