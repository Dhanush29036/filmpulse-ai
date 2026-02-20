"""
FilmPulse AI — Budget Optimization Model (Phase 3 Upgrade)
===========================================================
Architecture:
  1. Ridge Regression  → predict per-channel ROI
  2. Multi-Arm Bandit  → RL-style exploration/exploitation for budget reallocation
  3. Softmax Optimizer → convert ROI predictions to optimal allocation percentages

Input:  total_budget, target_region, genre, [cast_popularity, release_month]
Output: channel allocations (%), predicted ROI, RL-suggested reallocation
"""

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings("ignore")

# ── Channels & Domain Tables ──────────────────────────────────────────────────
CHANNELS = [
    "YouTube Ads",
    "Instagram & Reels",
    "Google Display",
    "TV Spots",
    "Outdoor / OOH",
    "Influencer Marketing",
    "Facebook Ads",
    "Twitter / X Ads",
]

GENRES   = ["Action", "Romance", "Thriller", "Comedy", "Drama", "Horror"]
REGIONS  = ["Pan-India", "North India", "South India", "Metro Cities", "Tier 2 Cities"]

CH = len(CHANNELS)

# ── Genre × Channel ROI multipliers (expert-designed) ────────────────────────
GENRE_MULT = np.array([
    #  YT     IG     GD     TV    OOH   INF    FB     TW
    [1.3,   1.1,   1.0,   0.9,  0.8,  1.2,  1.0,  1.1],  # Action
    [1.0,   1.4,   0.9,   0.9,  0.7,  1.3,  1.2,  0.9],  # Romance
    [1.2,   1.1,   1.1,   1.0,  0.9,  1.0,  1.0,  1.1],  # Thriller
    [1.1,   1.3,   0.9,   1.0,  0.8,  1.3,  1.1,  1.0],  # Comedy
    [0.9,   1.1,   1.0,   1.2,  1.0,  1.0,  1.1,  0.8],  # Drama
    [1.3,   1.2,   1.1,   0.8,  0.8,  1.4,  1.1,  1.2],  # Horror
])

# ── Region × Channel ROI multipliers ─────────────────────────────────────────
REGION_MULT = np.array([
    #  YT     IG     GD     TV    OOH   INF    FB     TW
    [1.0,   1.0,   1.0,   1.1,  1.1,  0.9,  1.0,  0.9],  # Pan-India
    [0.9,   1.1,   0.9,   1.2,  1.2,  0.8,  1.0,  0.8],  # North India
    [1.1,   0.9,   1.1,   0.9,  0.9,  1.1,  0.9,  1.0],  # South India
    [1.2,   1.3,   1.2,   0.8,  0.8,  1.3,  1.1,  1.2],  # Metro Cities
    [0.8,   0.9,   0.8,   1.3,  1.4,  0.7,  1.0,  0.7],  # Tier 2 Cities
])

# Base percentage allocation (must sum to 100)
BASE_PCTS = np.array([26.0, 22.0, 12.0, 13.0, 8.0, 10.0, 6.0, 3.0])
assert abs(BASE_PCTS.sum() - 100) < 1e-6

# ── Training Data (Ridge ROI per channel per scenario) ────────────────────────
rng = np.random.RandomState(99)

def _make_training_data(n=800):
    Xs, ys = [], []
    for _ in range(n):
        g_i  = rng.randint(0, len(GENRES))
        r_i  = rng.randint(0, len(REGIONS))
        b    = rng.uniform(5e5, 3e7)
        cp   = rng.uniform(2.0, 10.0)
        month = rng.randint(1, 13)
        # Seasonal multiplier (festive months get higher ROI)
        season = 1.15 if month in [10, 11, 12, 1] else (1.05 if month in [3, 4] else 1.0)

        raw = BASE_PCTS * GENRE_MULT[g_i] * REGION_MULT[r_i]
        alloc_vec = raw / raw.sum()

        for c_i in range(CH):
            roi = (
                0.8
                + GENRE_MULT[g_i, c_i] * 0.6
                + REGION_MULT[r_i, c_i] * 0.5
                + alloc_vec[c_i] * 2.5
                + (cp - 5) * 0.04
                + season * 0.1
                + rng.uniform(-0.25, 0.25)
            )
            Xs.append([g_i, r_i, c_i, np.log1p(b), alloc_vec[c_i], cp, month])
            ys.append(max(0.5, roi))

    return np.array(Xs), np.array(ys)

X_roi, y_roi = _make_training_data()

_roi_model = Pipeline([
    ("scaler", StandardScaler()),
    ("ridge",  Ridge(alpha=0.8)),
])
_roi_model.fit(X_roi, y_roi)


# ══════════════════════════════════════════════════════════════════════════════
# Multi-Arm Bandit (ε-greedy) — RL-style reallocation
# ══════════════════════════════════════════════════════════════════════════════
class EpsilonGreedyBandit:
    """
    Lightweight ε-greedy bandit to suggest exploration budget.
    Treats each channel as an arm. Uses Ridge ROI predictions as initial Q-values.
    """
    def __init__(self, n_arms: int, epsilon: float = 0.12, seed: int = 7):
        self.n    = n_arms
        self.eps  = epsilon
        self.rng  = np.random.RandomState(seed)
        self.Q    = np.ones(n_arms)   # Q-value (expected ROI per arm)
        self.N    = np.zeros(n_arms)  # times arm was chosen

    def seed_with_roi(self, roi_predictions: np.ndarray):
        """Initialise Q-values with Ridge ROI predictions."""
        self.Q = np.array(roi_predictions, dtype=float)

    def select_allocation(self, base_pcts: np.ndarray, explore_budget_pct: float = 0.08):
        """
        Return RL-adjusted allocation percentages.
        explore_budget_pct: fraction of budget to reallocate toward exploration arm.
        """
        # ε-greedy: pick exploration arm
        if self.rng.uniform() < self.eps:
            explore_arm = self.rng.randint(self.n)
        else:
            explore_arm = int(np.argmax(self.Q))

        # Pull explore_budget_pct from lowest Q-value arm
        worst_arm    = int(np.argmin(self.Q))
        adjusted     = base_pcts.copy().astype(float)
        transfer     = min(adjusted[worst_arm] * 0.5, explore_budget_pct * 100)
        adjusted[worst_arm]   -= transfer
        adjusted[explore_arm] += transfer

        # Re-normalise
        adjusted = np.clip(adjusted, 1.0, None)
        adjusted = adjusted / adjusted.sum() * 100

        self.N[explore_arm] += 1
        return adjusted, explore_arm

_bandit = EpsilonGreedyBandit(n_arms=CH)


# ── Softmax Allocation ────────────────────────────────────────────────────────
def _softmax_allocation(roi_preds: np.ndarray, temperature: float = 0.5) -> np.ndarray:
    """Convert ROI predictions to allocation % via softmax (temperature-controlled)."""
    scaled = roi_preds / temperature
    exp    = np.exp(scaled - np.max(scaled))
    return (exp / exp.sum()) * 100


# ── Public API ────────────────────────────────────────────────────────────────
def optimize_budget(
    total_budget: float,
    target_region: str,
    genre: str,
    cast_popularity: float = 7.0,
    release_month: int = 6,
) -> dict:
    """
    Optimise marketing budget across channels.

    Steps:
      1. Build allocation from genre × region multipliers
      2. Predict ROI per channel via Ridge Regression
      3. Softmax-adjust allocation based on ROI predictions
      4. Apply ε-greedy bandit for exploration adjustment
      5. Return full channel breakdown + RL suggestion
    """
    g_i = GENRES.index(genre)  if genre  in GENRES  else 0
    r_i = REGIONS.index(target_region) if target_region in REGIONS else 0

    # Step 1 — base allocation from expert matrix
    raw  = BASE_PCTS * GENRE_MULT[g_i] * REGION_MULT[r_i]
    base_pcts = np.round((raw / raw.sum()) * 100).astype(float)

    # Step 2 — Ridge ROI prediction per channel
    roi_preds = []
    for c_i, alloc in enumerate(base_pcts / 100.0):
        feat = np.array([[g_i, r_i, c_i, np.log1p(total_budget),
                          alloc, cast_popularity, release_month]])
        roi_preds.append(float(_roi_model.predict(feat)[0]))
    roi_arr = np.array(roi_preds)

    # Step 3 — Softmax-adjusted allocation
    softmax_pcts = _softmax_allocation(roi_arr, temperature=0.6)

    # Step 4 — RL bandit adjustment
    _bandit.seed_with_roi(roi_arr)
    rl_pcts, explore_arm = _bandit.select_allocation(softmax_pcts)
    rl_pcts_rounded = np.round(rl_pcts).astype(int)
    # Fix rounding drift
    diff = 100 - rl_pcts_rounded.sum()
    rl_pcts_rounded[explore_arm] += diff

    budgets = (rl_pcts_rounded / 100.0) * total_budget
    best_roi_idx = int(np.argmax(roi_preds))
    blended_roi  = round(float(np.dot(roi_arr, rl_pcts_rounded / 100.0)), 3)

    channels_out = [
        {
            "name":           CHANNELS[i],
            "allocation_pct": int(rl_pcts_rounded[i]),
            "budget_inr":     round(float(budgets[i])),
            "estimated_roi":  round(roi_preds[i], 2),
            "recommended":    i == best_roi_idx,
            "rl_explore":     i == explore_arm,
        }
        for i in range(CH)
    ]

    return {
        "total_budget":          total_budget,
        "target_region":         target_region,
        "genre":                 genre,
        "channels":              channels_out,
        "total_predicted_return": round(total_budget * blended_roi),
        "blended_roi":           blended_roi,
        "top_channel":           CHANNELS[best_roi_idx],
        "rl_explore_channel":    CHANNELS[explore_arm],
        "model": ("Ridge Regression (ROI) + ε-Greedy Bandit (RL allocation) "
                  "+ Softmax Temperature Scaling — trained on 800 synthetic records"),
    }
