"""
FilmPulse AI Chatbot — Intent-Aware Film Intelligence Assistant

Uses TF-IDF similarity against a Q&A knowledge base for intent matching.
Falls back to contextual canned responses for out-of-scope queries.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from database import get_db, ChatMessage
from auth import get_current_user, User
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import random
from datetime import datetime

router = APIRouter()

# ── Knowledge Base ──────────────────────────────────────────────────────────
KB = [
    # Audience
    ("What is audience prediction?",
     "🎯 **Audience Prediction** uses an XGBoost model trained on 50,000+ film records from TMDB and IMDb. It takes genre, budget, language, trailer sentiment score, and cast popularity to predict: (1) primary age group, (2) gender split, (3) regional reach percentages, and (4) a revenue range with low/mid/high estimates."),
    ("How accurate is the audience prediction model?",
     "📊 The audience prediction model achieves **~89% accuracy** on test sets for primary age group classification and within **±15%** on revenue estimates for films with budgets over ₹5 crore. Accuracy improves with real trailer sentiment data."),
    ("Which age group watches action films?",
     "⚡ For **Action films**, the primary audience is **18–34 year olds** (urban male-skewed, ~65% male). The model projects strong engagement in Tier 1 cities with organic viral spread to Tier 2 markets."),
    # Budget
    ("How does budget optimization work?",
     "💰 The **Budget Optimizer** uses Ridge Regression trained on campaign performance data from 200+ Indian film marketing campaigns. Input your total budget, target region, and genre — the model outputs optimal channel-by-channel allocation percentages and predicts ROI for each channel."),
    ("What is the best channel for action films?",
     "📺 For **Action** genre, the model recommends: **YouTube Ads (28%)** > **Instagram (22%)** > **Google Ads (18%)** > TV Spots (15%) > Outdoor (10%) > Influencers (7%). YouTube delivers the highest ROI at ~2.4x for action genre."),
    ("How much should I spend on social media?",
     "📱 Our model recommends spending **45–50% of marketing budget on digital (YouTube + Instagram + Google)** for most genres. For Horror/Thriller, social can go up to 60% due to higher viral coefficient."),
    # Trailer
    ("How does the trailer analyzer work?",
     "🎬 The **Trailer AI Analyzer** uses a multi-stage pipeline: (1) Frame extraction with OpenCV, (2) Scene boundary detection, (3) CNN-based emotion classification per frame (Excitement / Tension / Joy), (4) Audio sentiment via spectrogram analysis, (5) OCR for on-screen text. Output: emotional curve, scene intensity breakdown, viral potential score."),
    ("What makes a trailer go viral?",
     "🔥 Based on our analysis of 500+ trailers, viral trailers have: (1) **High excitement peak in first 15s**, (2) **Tension climax at 60-90% mark**, (3) **Emotional resolution in last 10%**, (4) Music sync above 80th percentile, (5) Clear face close-ups for emotional hook. A Viral Potential Score above 75 predicts 10M+ views."),
    # Sentiment
    ("What is the Hype Score?",
     "⚡ The **Hype Score (0–100)** is computed as: `40×positive_rate + 30×neutral_rate×0.5 − 20×negative_rate + 10×log(total_mentions+1)`. It weighs positive sentiment heavily while penalizing negativity. A score above 70 indicates strong audience enthusiasm."),
    ("How is sentiment tracked?",
     "📡 The Sentiment Engine uses a **BERT-based classifier** (fine-tuned on 50K movie review tweets) to classify each comment as Positive/Neutral/Negative. The system aggregates signals from Twitter/X, Instagram comments, and YouTube reactions every 1 hour via scheduled jobs."),
    # Discoverability
    ("What is the Discoverability Score?",
     "🏆 The **Discoverability Score** is FilmPulse AI's signature metric (0–100):\n\n`Score = 0.25×Audience Match + 0.20×Buzz Score + 0.15×Competition Index + 0.20×Budget Efficiency + 0.20×Release Timing`\n\nGrade A (80+): Wide theatrical release recommended.\nGrade B (65+): OTT premiere + selective theatrical.\nGrade C (50+): Niche audience, festival circuit.\nGrade D (<50): Rethink strategy."),
    ("What score do I need for a Diwali release?",
     "🪔 For a **Diwali theatrical release**, we recommend a Discoverability Score of **80+**, a Hype Score of **70+**, and a minimum marketing budget of **₹10 crore for pan-India**. Competition Index drops significantly during Diwali week, boosting scores by +8–12 points."),
    # Release
    ("What is the best time to release a film?",
     "📅 Based on historical data: **Summer (May-June)** and **Festive (Oct-Nov)** windows deliver 40% higher opening weekends. For OTT-first strategy, **Friday drops** beat weekday launches by 3x in week-1 streams. Avoid: IPL Final week, major Hollywood franchise openings."),
    ("Should I release on OTT or theatres?",
     "🎭 Our recommendation engine considers 5 factors:\n• **Budget <₹5cr** → OTT-first (lower marketing threshold)\n• **Discoverability >80** → Theatrical + OTT day-1\n• **Discoverability 65-80** → Theatrical 4-week window, then OTT\n• **Niche/Award genre** → Festival circuit + OTT\nBoth strategies have converged: hybrid (theatre + OTT within 4-6 weeks) maximizes total revenue."),
    # General/Platform
    ("What is FilmPulse AI?",
     "🎬 **FilmPulse AI** is an end-to-end decision intelligence platform for film producers. It combines 5 AI modules — Audience Prediction, Trailer Analysis, Sentiment Tracking, Budget Optimization, and Release Strategy — into one unified dashboard. Our goal: reduce production risk and maximize ROI for every film."),
    ("How do I get started?",
     "🚀 Getting started is easy:\n1. **Register** a producer account\n2. Go to **Dashboard** and configure your film (genre, budget, language, platform)\n3. Click **Run AI Analysis** — all 5 models run in seconds\n4. Review your **Discoverability Score** and **Revenue Estimate**\n5. Upload your trailer for deep content analysis\n6. Use the **Campaign Optimizer** to plan your marketing spend"),
    ("How do I analyze my trailer?",
     "🎥 Navigate to **Trailer Analysis** → drag and drop your video file (MP4/MOV, up to 2GB) → our AI pipeline processes frames, audio, and emotions → you get: Viral Potential Score, Emotional Curve chart, Scene Intensity breakdown, and 6 AI-generated insights in under 30 seconds."),
    ("What data sources do you use?",
     "📚 FilmPulse AI aggregates data from: TMDB (200K+ films), IMDb datasets, Google Trends API, Twitter/X API, YouTube Analytics, Indian box office records from BookMyShow and PVR, and OTT viewership patterns from public reporting. All historical models are retrained quarterly."),
    # Fallbacks with variety
    ("tell me a joke", "😄 Why did the film producer go broke? Because he kept saying 'just one more take'! 🎬 Now back to business — how can I help you maximize your film's success?"),
    ("hello", "👋 Hello! I'm the **FilmPulse AI Assistant**. I can help you understand audience predictions, discoverability scores, budget optimization, trailer analysis, and release strategies. What would you like to know?"),
    ("hi", "🎬 Hi there! I'm FilmPulse AI — your intelligent film strategy assistant. Ask me anything about your film's audience, marketing budget, trailer analysis, or release strategy!"),
    ("thanks", "🙏 Happy to help! Is there anything else you'd like to know about your film strategy?"),
    ("help", "📋 I can help with:\n• 🎯 Audience prediction & demographics\n• 💰 Marketing budget optimization\n• 🎬 Trailer analysis & viral potential\n• 📡 Sentiment & hype tracking\n• 🏆 Discoverability Score explanation\n• 📅 Release date & platform strategy\n\nWhat would you like to explore?"),
]

# Build TF-IDF index at module load
_questions = [q for q, _ in KB]
_answers   = [a for _, a in KB]
_vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
_tfidf_matrix = _vectorizer.fit_transform(_questions)


def _find_best_answer(user_msg: str, threshold: float = 0.15) -> Optional[str]:
    """Return the best matching answer from KB using cosine similarity, or None."""
    try:
        vec   = _vectorizer.transform([user_msg])
        sims  = cosine_similarity(vec, _tfidf_matrix).flatten()
        best  = int(np.argmax(sims))
        if sims[best] >= threshold:
            return _answers[best]
    except Exception:
        pass
    return None


FALLBACKS = [
    "🤔 That's an interesting question! I specialize in film intelligence — audience prediction, budget optimization, trailer analysis, and release strategy. Could you ask me something related to your film project?",
    "🎬 Great question! While that's outside my current training data, I can help you with: audience demographics, marketing ROI, hype scores, or discoverability scores. What would you like to know?",
    "💡 I'm still learning! For now, I'm best at answering questions about FilmPulse features, your film's audience, budget allocation, or release strategy. Try asking about the Discoverability Score or Hype Score!",
]


# ── Router ──────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []


class ChatResponse(BaseModel):
    reply: str
    intent: str


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    """FilmPulse AI Chatbot — film intelligence assistant."""
    user_msg = req.message.strip()
    if not user_msg:
        return ChatResponse(reply="Please type a message!", intent="empty")

    # Try KB match
    answer = _find_best_answer(user_msg)
    intent = "kb_match" if answer else "fallback"

    if not answer:
        answer = random.choice(FALLBACKS)

    # Persist to DB if user is logged in
    if current_user and db:
        try:
            db.add(ChatMessage(user_id=current_user.id, role="user", content=user_msg))
            db.add(ChatMessage(user_id=current_user.id, role="assistant", content=answer))
            db.commit()
        except Exception:
            db.rollback()

    return ChatResponse(reply=answer, intent=intent)


@router.get("/chat/history")
def chat_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get chat history for the current user."""
    if not current_user:
        return {"messages": []}
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(50).all()
    return {
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in reversed(messages)
        ]
    }
