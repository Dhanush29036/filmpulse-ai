"""
FilmPulse AI — Audience Prediction Model (Phase 3 Upgrade)
============================================================
Upgraded to XGBoost for revenue prediction + RandomForest for age classification.
Adds region probability distribution and OTT/theatrical split prediction.

Input:  genre, budget, language, trailer_sentiment, cast_popularity
Output: primary_age_group, region_probability, revenue_range, OTT estimate
"""
import numpy as np
import warnings
warnings.filterwarnings("ignore")

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
try:
    from xgboost import XGBRegressor, XGBClassifier
    _HAS_XGB = True
except ImportError:
    from sklearn.ensemble import GradientBoostingRegressor as XGBRegressor
    from sklearn.ensemble import GradientBoostingClassifier as XGBClassifier
    _HAS_XGB = False

# ── Domain Knowledge Tables ───────────────────────────────────────────────────
GENRES     = ["Action", "Romance", "Thriller", "Comedy", "Drama", "Horror"]
LANGUAGES  = ["Hindi", "English", "Tamil", "Telugu", "Bengali", "Marathi"]
AGE_GROUPS = ["13-17", "18-24", "25-34", "35-44", "45+"]
REGIONS    = ["North India", "South India", "East India", "West India",
              "Metro Cities", "Tier 2 Cities", "International"]

GENRE_PROFILES = {
    "Action":   {"base_mult": 2.2, "primary_age": "18-24", "male": 65, "female": 35, "urban": 75,
                 "regions": [0.20, 0.18, 0.12, 0.22, 0.18, 0.08, 0.02]},
    "Romance":  {"base_mult": 1.8, "primary_age": "18-24", "male": 35, "female": 65, "urban": 65,
                 "regions": [0.25, 0.15, 0.15, 0.20, 0.16, 0.07, 0.02]},
    "Thriller": {"base_mult": 2.0, "primary_age": "25-34", "male": 58, "female": 42, "urban": 72,
                 "regions": [0.18, 0.20, 0.12, 0.20, 0.20, 0.07, 0.03]},
    "Comedy":   {"base_mult": 1.7, "primary_age": "18-24", "male": 50, "female": 50, "urban": 60,
                 "regions": [0.22, 0.16, 0.14, 0.20, 0.16, 0.10, 0.02]},
    "Drama":    {"base_mult": 1.5, "primary_age": "25-34", "male": 45, "female": 55, "urban": 68,
                 "regions": [0.20, 0.18, 0.16, 0.18, 0.17, 0.09, 0.02]},
    "Horror":   {"base_mult": 1.6, "primary_age": "18-24", "male": 55, "female": 45, "urban": 80,
                 "regions": [0.18, 0.16, 0.10, 0.20, 0.25, 0.09, 0.02]},
}

LANG_REACH = {
    "Hindi":   {"reach": 0.88, "ott_mult": 1.1},
    "English": {"reach": 0.72, "ott_mult": 1.3},
    "Tamil":   {"reach": 0.65, "ott_mult": 0.9},
    "Telugu":  {"reach": 0.67, "ott_mult": 0.95},
    "Bengali": {"reach": 0.55, "ott_mult": 0.85},
    "Marathi": {"reach": 0.50, "ott_mult": 0.80},
}

# ── Feature Engineering ───────────────────────────────────────────────────────
def _build_features(genre, language, budget, trailer_sentiment, cast_popularity):
    """Generate enriched feature vector (9 features)."""
    g_idx    = GENRES.index(genre) if genre in GENRES else 0
    l_idx    = LANGUAGES.index(language) if language in LANGUAGES else 0
    log_b    = np.log1p(budget)
    norm_b   = min(1.0, budget / 2e8)         # normalised budget 0-1
    ts       = float(trailer_sentiment)
    cp       = float(cast_popularity)
    genre_am = GENRE_PROFILES.get(genre, GENRE_PROFILES["Action"])["base_mult"] / 2.5
    lang_r   = LANG_REACH.get(language, {"reach": 0.7})["reach"]
    buzz_proxy = (ts * 0.5 + cp / 10 * 0.5)  # synthetic buzz from inputs
    return np.array([[g_idx, l_idx, log_b, norm_b, ts, cp, genre_am, lang_r, buzz_proxy]])

# ── Synthetic Training Data ───────────────────────────────────────────────────
rng = np.random.RandomState(42)

def _generate_training_data(n=1200):
    X, y_rev, y_age = [], [], []
    for _ in range(n):
        g  = rng.choice(GENRES)
        l  = rng.choice(LANGUAGES)
        b  = rng.uniform(5e5, 3e8)
        ts = rng.uniform(0.25, 0.98)
        cp = rng.uniform(2.0, 10.0)
        prof = GENRE_PROFILES[g]
        noise = rng.uniform(-0.25, 0.25)
        lang_info  = LANG_REACH.get(l, {"reach": 0.7})
        rev_mult = (prof["base_mult"]
                    * (0.6 + ts * 0.7)
                    * (0.75 + (cp - 5) * 0.09)
                    * lang_info["reach"]
                    + noise)
        age_idx = AGE_GROUPS.index(prof["primary_age"]) + rng.randint(-1, 2)
        age_idx = max(0, min(len(AGE_GROUPS) - 1, age_idx))

        g_idx   = GENRES.index(g)
        l_idx   = LANGUAGES.index(l)
        log_b   = np.log1p(b)
        norm_b  = min(1.0, b / 2e8)
        genre_am = prof["base_mult"] / 2.5
        buzz_proxy = ts * 0.5 + cp / 10 * 0.5
        X.append([g_idx, l_idx, log_b, norm_b, ts, cp, genre_am, lang_info["reach"], buzz_proxy])
        y_rev.append(max(0.4, rev_mult))
        y_age.append(age_idx)

    return np.array(X), np.array(y_rev), np.array(y_age)

X_train, y_rev, y_age = _generate_training_data()

# ── Train XGBoost / GBR Revenue Model ────────────────────────────────────────
if _HAS_XGB:
    _revenue_model = XGBRegressor(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        reg_alpha=0.1, reg_lambda=1.0,
        random_state=42, verbosity=0
    )
else:
    _revenue_model = XGBRegressor(
        n_estimators=150, max_depth=5, learning_rate=0.06, random_state=42
    )
_revenue_model.fit(X_train, y_rev)

# ── Train RF Age Group Classifier ─────────────────────────────────────────────
_age_model = RandomForestClassifier(
    n_estimators=150, max_depth=6,
    min_samples_leaf=3, random_state=42
)
_age_model.fit(X_train, y_age)

# ── Region Probability Model (RF multi-output) ────────────────────────────────
# Target: 7 region probability columns
y_regions = np.zeros((len(X_train), len(REGIONS)))
for i in range(len(X_train)):
    g_name = GENRES[int(X_train[i, 0])]
    base_r = np.array(GENRE_PROFILES[g_name]["regions"])
    noise_r = rng.uniform(-0.04, 0.04, len(REGIONS))
    r = np.clip(base_r + noise_r, 0, 1)
    y_regions[i] = r / r.sum()

_region_model = RandomForestRegressor(
    n_estimators=80, max_depth=4, random_state=42
)
_region_model.fit(X_train, y_regions)


# ── Public API ────────────────────────────────────────────────────────────────
def predict_audience(genre: str, budget: float, language: str,
                     trailer_sentiment: float, cast_popularity: float) -> dict:
    """
    Run XGBoost revenue + RF age + RF region models.
    Returns rich audience prediction dict.
    """
    genre    = genre if genre in GENRES else "Action"
    language = language if language in LANGUAGES else "Hindi"

    X = _build_features(genre, language, budget, trailer_sentiment, cast_popularity)

    rev_mult  = float(_revenue_model.predict(X)[0])
    age_probs = _age_model.predict_proba(X)[0]
    age_idx   = int(_age_model.predict(X)[0])
    reg_probs = np.clip(_region_model.predict(X)[0], 0, 1)
    reg_probs = reg_probs / reg_probs.sum()  # normalise

    prof     = GENRE_PROFILES.get(genre, GENRE_PROFILES["Action"])
    lang_info = LANG_REACH.get(language, {"reach": 0.7, "ott_mult": 1.0})
    rev_mid  = budget * rev_mult
    rev_low  = rev_mid * 0.68
    rev_high = rev_mid * 1.60

    # Age distribution (normalised to 100)
    raw_age  = {AGE_GROUPS[i]: max(2, int(p * 100)) for i, p in enumerate(age_probs)}
    total    = sum(raw_age.values()) or 1
    age_dist = {k: round(v / total * 100) for k, v in raw_age.items()}

    # Region probabilities (%)
    region_prob = {REGIONS[i]: round(float(reg_probs[i]) * 100, 1) for i in range(len(REGIONS))}

    # OTT estimates
    ott_mult = lang_info.get("ott_mult", 1.0)
    week1_ott  = int(rev_mid / 1e6 * 140_000 * ott_mult)
    month1_ott = int(rev_mid / 1e6 * 420_000 * ott_mult)

    model_tag = ("XGBoost" if _HAS_XGB else "GradientBoosting") + " + RandomForest"

    return {
        "genre":    genre,
        "language": language,
        "budget":   budget,

        # Audience demographics
        "primary_age_group":      AGE_GROUPS[age_idx],
        "age_group_distribution": age_dist,
        "gender_split":           {"male": prof["male"], "female": prof["female"]},
        "urban_rural_split":      {"urban": prof["urban"], "rural": 100 - prof["urban"]},
        "region_probability":     region_prob,
        "pan_india_reach_pct":    round(lang_info["reach"] * 100, 1),

        # Revenue
        "revenue_multiplier": round(rev_mult, 3),
        "revenue_estimate": {
            "low":  round(rev_low  / 1e6, 2),
            "mid":  round(rev_mid  / 1e6, 2),
            "high": round(rev_high / 1e6, 2),
            "unit": "million INR",
        },
        "ott_views_estimate": {
            "week_1":  week1_ott,
            "month_1": month1_ott,
        },

        # Model metadata
        "genre_score": round(min(1.0, max(0.1, rev_mult / 3.0)), 3),
        "model": f"{model_tag} — trained on 1200 synthetic Bollywood-pattern records",
        "xgboost_available": _HAS_XGB,
    }
