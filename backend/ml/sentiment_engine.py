"""
FilmPulse AI — Sentiment Engine (Phase 3 Upgrade)
===================================================
Architecture:
  Primary:  HuggingFace distilbert-base-uncased-finetuned-sst-2-english (BERT-based)
  Fallback: MultinomialNB + TF-IDF (always available, no GPU needed)

The BERT model loads lazily on first use and is cached.
All endpoints remain fast via the NB fallback when transformers is unavailable.

Output: Hype Score (0-100), pos/neu/neg %, sentiment_label, top comments
"""

import numpy as np
import math
import warnings
from typing import List, Optional
warnings.filterwarnings("ignore")

# ── Try HuggingFace Transformers ──────────────────────────────────────────────
_bert_pipeline = None
_HAS_TRANSFORMERS = False

def _load_bert():
    """Lazy-load BERT sentiment pipeline (cached after first call)."""
    global _bert_pipeline, _HAS_TRANSFORMERS
    if _bert_pipeline is not None:
        return _bert_pipeline
    try:
        from transformers import pipeline as hf_pipeline
        _bert_pipeline = hf_pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            truncation=True,
            max_length=512,
        )
        _HAS_TRANSFORMERS = True
        print("[SentimentEngine] BERT model loaded (distilbert-sst2)")
    except Exception as e:
        print(f"[SentimentEngine] HuggingFace unavailable ({e}), using NB+TF-IDF fallback")
        _bert_pipeline = None
    return _bert_pipeline

# ── NB + TF-IDF Fallback ─────────────────────────────────────────────────────
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV

_POSITIVE = [
    "This film looks amazing I can't wait to watch it",
    "The trailer is absolutely brilliant and epic must watch",
    "Best movie of the year for sure blockbuster guaranteed",
    "Incredible performances and stunning cinematography breathtaking",
    "This is going to be a blockbuster for sure hit",
    "The music is fire and the cast is fantastic brilliant",
    "Mind-blowing action sequences absolutely loved every moment",
    "What a masterpiece deeply emotional and powerful filmmaking",
    "Standing ovation this film is extraordinary pure gold",
    "Perfect storytelling and visually breathtaking cinematic experience",
    "I am so hyped for this release cannot wait opening day",
    "This film gave me chills the acting is completely superb",
    "The direction is brilliant this is must watch film",
    "Loved every frame of this trailer pure cinematic gold",
    "This is exactly what cinema should be wonderful art",
    "Outstanding performances and gripping storyline throughout entire film",
    "The background score alone is worth watching for gold",
    "Cinema at its finest this film is a genuine gem",
    "Absolutely captivating from first frame to last second",
    "This director is a genius visionary storytelling mastery",
    "I cried watching this trailer that is saying something special",
    "The villain in this looks absolutely terrifying amazing casting",
    "Best casting choice I have ever seen in many years",
    "This will sweep all awards definitely a landmark film",
    "Cannot believe how good this looks so excited now",
    "Shah Rukh Khan looks phenomenal in this role incredible",
    "The VFX are out of this world for an Indian film",
    "Goosebumps from start to end of the trailer wow",
    "This is going to be historical film of our generation",
    "Already booked tickets for the opening weekend so excited",
] * 10

_NEGATIVE = [
    "This film looks terrible and boring please skip it",
    "Worst trailer I have ever seen in my entire life",
    "Absolutely disappointing and predictable storyline from start to end",
    "I am so tired of this same old formula again",
    "Terrible acting and horrible script complete waste of time",
    "This looks like a flop for sure overrated star cast",
    "Mediocre at best will wait for it on OTT streaming",
    "Another cash grab sequel nobody actually asked for this",
    "The CGI looks fake and the story is completely bland",
    "Please stop making these formulaic films cinema is dying badly",
    "Bad direction and the editing is a complete terrible mess",
    "Overrated actor ruining another potentially good story sadly",
    "This is going to bomb at the box office definitely",
    "Cringe worthy dialogue and extremely poor character development shown",
    "Totally unoriginal and derivative just rehashing tired old ideas",
    "The cinematography is terrible and the music is irritating",
    "Nothing new or interesting to offer here at all unfortunately",
    "I fell asleep watching this trailer that is really bad",
    "Complete disaster of a film deeply regret watching this trailer",
    "This franchise needs to end immediately enough is enough now",
    "The script looks like it was written in one hour",
    "Every cliche in the book has been thrown in here",
    "This director has clearly lost the plot entirely sad",
    "The lead actor is completely miscast wrong choice entirely",
    "Why would anyone spend money to watch this nonsense",
] * 8

_NEUTRAL = [
    "The trailer looks okay will definitely wait for reviews first",
    "Interesting concept but need to see the full film first",
    "Some parts look good some parts look very average honestly",
    "Will decide after the first weekend reviews start coming in",
    "The cast is alright the story might be okay enough",
    "Looks like a decent film for a casual family outing",
    "Mixed feelings about this one but will give it chance",
    "Not my usual genre but I might watch it anyway",
    "The trailer does not reveal much which is neutral approach",
    "Waiting for more information before forming a strong opinion",
    "Could be good or bad honestly hard to tell from this",
    "Modest expectations going in but open to being surprised",
    "The lead actor is decent but the story seems familiar",
    "Might watch if friends want to go otherwise probably skip",
    "Heard mixed things about this one not sure yet",
    "Average trailer average film probably average box office collection",
    "Nothing spectacular but nothing terrible either just okay",
    "Wait and watch approach for now lets see the reviews",
] * 12

_X_text  = _POSITIVE + _NEGATIVE + _NEUTRAL
_y_label = (["positive"] * len(_POSITIVE)
           + ["negative"] * len(_NEGATIVE)
           + ["neutral"]  * len(_NEUTRAL))

# Train with ComplementNB (better for imbalanced text datasets)
_nb_pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=5000,
        sublinear_tf=True,
        strip_accents="unicode",
        min_df=1,
    )),
    ("clf", ComplementNB(alpha=0.3)),
])
_nb_pipeline.fit(_X_text, _y_label)

# ── BERT scoring helper ───────────────────────────────────────────────────────
def _bert_classify(texts: List[str]):
    """Run HuggingFace BERT pipeline, map POSITIVE/NEGATIVE to our 3 classes."""
    pipe = _load_bert()
    if pipe is None:
        return None

    labels = []
    for text in texts:
        try:
            result = pipe(text[:512])[0]
            raw = result["label"].upper()
            score = result["score"]
            if raw == "POSITIVE":
                labels.append("positive" if score > 0.70 else "neutral")
            else:  # NEGATIVE
                labels.append("negative" if score > 0.70 else "neutral")
        except Exception:
            labels.append("neutral")
    return labels


# ── Keyword Extraction ────────────────────────────────────────────────────────
_STOPWORDS = {"i", "me", "my", "the", "a", "an", "this", "it", "is", "was",
              "are", "for", "to", "of", "on", "in", "and", "or", "but", "so",
              "be", "will", "have", "has", "had", "at", "by", "as", "with"}

def _extract_keywords(comments: List[str], label_filter: str,
                       labels: List[str], top_n: int = 8) -> List[str]:
    """Simple TF-based keyword extraction for a sentiment class."""
    texts = [c for c, l in zip(comments, labels) if l == label_filter]
    if not texts:
        return []
    freq = {}
    for t in texts:
        for w in t.lower().split():
            w = w.strip(".,!?\"'#@")
            if len(w) > 3 and w not in _STOPWORDS:
                freq[w] = freq.get(w, 0) + 1
    return sorted(freq, key=freq.get, reverse=True)[:top_n]


# ── Public API ────────────────────────────────────────────────────────────────
def compute_sentiment(comments: List[str], use_bert: bool = True) -> dict:
    """
    Classify comments and compute a Hype Score (0-100).

    Strategy:
      1. Try HuggingFace BERT (distilbert-sst2) if use_bert=True and available
      2. Fall back to ComplementNB + TF-IDF (always works)

    Hype Score formula:
      hype = 40×pos_ratio + 15×neu_ratio - 25×neg_ratio + 10×log(n+1) + sentiment_bonus
    """
    if not comments:
        return {
            "hype_score": 0, "positive": 0, "neutral": 0, "negative": 0,
            "total_analyzed": 0, "positive_pct": 0, "neutral_pct": 0,
            "negative_pct": 0, "sentiment_label": "No Data",
            "model": "no data",
        }

    # Pick classifier
    labels = None
    model_tag = "ComplementNB + TF-IDF (ngram 1-3, 5000 features)"
    if use_bert:
        labels = _bert_classify(comments)
        if labels:
            model_tag = "distilbert-base-uncased-finetuned-sst-2-english (HuggingFace)"
    if labels is None:
        labels = list(_nb_pipeline.predict(comments))

    total   = len(labels)
    pos     = labels.count("positive")
    neu     = labels.count("neutral")
    neg     = labels.count("negative")
    pos_r   = pos / total
    neu_r   = neu / total
    neg_r   = neg / total

    # Hype Score — weighted formula
    scale      = 10 * math.log(total + 1)
    base_score = 40 * pos_r + 15 * neu_r - 25 * neg_r + scale
    # Bonus: if strongly positive (>70% positive), boost
    bonus = 8 if pos_r > 0.70 else (4 if pos_r > 0.55 else 0)
    hype  = max(0, min(100, round(base_score + bonus)))

    # Sentiment label
    if   hype >= 75: label = "Strongly Positive 🔥"
    elif hype >= 60: label = "Positive Buzz 👍"
    elif hype >= 45: label = "Mixed Signals 🤔"
    elif hype >= 30: label = "Muted Reception 😐"
    else:            label = "Negative Buzz ⚠️"

    top_keywords = _extract_keywords(comments, "positive", labels)

    probs = _nb_pipeline.predict_proba(comments) if not _HAS_TRANSFORMERS else None
    avg_confidence = (float(np.mean(np.max(probs, axis=1))) if probs is not None else None)

    return {
        "hype_score":       hype,
        "total_analyzed":   total,
        "positive":         pos,
        "neutral":          neu,
        "negative":         neg,
        "positive_pct":     round(pos_r * 100, 1),
        "neutral_pct":      round(neu_r * 100, 1),
        "negative_pct":     round(neg_r * 100, 1),
        "sentiment_label":  label,
        "top_keywords":     top_keywords,
        "top_positive_comments": [c for c, l in zip(comments, labels) if l == "positive"][:3],
        "top_negative_comments": [c for c, l in zip(comments, labels) if l == "negative"][:2],
        "avg_confidence":   round(avg_confidence, 3) if avg_confidence else None,
        "bert_used":        _HAS_TRANSFORMERS and use_bert,
        "model":            model_tag,
    }
