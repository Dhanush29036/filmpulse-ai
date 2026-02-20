"""
FilmPulse AI — Analysis Router (Phase 4 / fully wired)
=======================================================
GET  /analyze-trailer     — Full CV pipeline (OpenCV/simulation)
GET  /predict-audience    — XGBoost + RF audience prediction
GET  /sentiment-analysis  — BERT / ComplementNB sentiment + hype score
POST /sentiment-batch     — [Producer/Admin] Batch comment analysis
"""
from fastapi import APIRouter, Query, Depends, Body
from pydantic import BaseModel
from typing import List, Optional
from ml.audience_model import predict_audience
from ml.sentiment_engine import compute_sentiment
from ml.discoverability import compute_discoverability_score
from ml.trailer_analyzer import run_trailer_pipeline
from mongo_db import upsert_trailer_analysis
from auth import get_current_user, require_producer_or_admin
from database import User

router = APIRouter()


class TrailerAnalysisResult(BaseModel):
    filename: str
    viral_potential: int
    engagement_score: int
    emotional_peak: int
    tension_index: int
    emotional_curve: List[int]
    scene_intensity: List[int]
    emotion_labels: Optional[List[str]] = None
    pacing_score: Optional[float] = None
    audio_sync_score: Optional[int] = None
    meme_potential: Optional[int] = None
    ocr_texts: Optional[List[str]] = None
    insights: List[str]
    opencv_used: Optional[bool] = False
    model_version: Optional[str] = None


@router.get("/analyze-trailer")
def analyze_trailer(
    filename:   str = Query("trailer.mp4"),
    film_id:    str = Query(""),
    video_path: str = Query(""),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Full Trailer AI Pipeline (Phase 3 + 4):
      1. Frame extraction       (OpenCV)
      2. Scene detection        (histogram shot boundaries)
      3. Emotion classification (SVM on 8-D visual features)
      4. Audio sentiment proxy  (bass energy, tempo, spectral flux)
      5. OCR text extraction    (pytesseract)
    Falls back to realistic simulation when no video_path is provided.
    Persists results to MongoDB trailer_analysis collection.
    """
    data = run_trailer_pipeline(
        video_path=video_path,
        filename=filename,
        film_id=film_id,
    )

    result = TrailerAnalysisResult(
        filename=data["filename"],
        viral_potential=data["viral_potential"],
        engagement_score=data["engagement_score"],
        emotional_peak=data["emotional_peak"],
        tension_index=data["tension_index"],
        emotional_curve=data["emotional_curve"],
        scene_intensity=data["scene_intensity"],
        emotion_labels=data.get("emotion_labels"),
        pacing_score=data.get("pacing_score"),
        audio_sync_score=data.get("audio_sync_score"),
        meme_potential=data.get("meme_potential"),
        ocr_texts=data.get("ocr_texts"),
        insights=data["insights"],
        opencv_used=data.get("opencv_used", False),
        model_version=data.get("model_version", "v3-phase3"),
    )

    if film_id:
        upsert_trailer_analysis(film_id, {**data, "model_version": "v3-phase4"})

    return result


@router.get("/predict-audience")
def predict_audience_endpoint(
    genre:             str   = Query("Action"),
    budget:            float = Query(8_000_000),
    language:          str   = Query("Hindi"),
    trailer_sentiment: float = Query(0.75),
    cast_popularity:   float = Query(7.5),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Predict target audience demographics and revenue range.
    Uses XGBoost for revenue (falls back to GBR) + RandomForest for region probability.
    """
    result = predict_audience(genre, budget, language, trailer_sentiment, cast_popularity)
    return result


@router.get("/sentiment-analysis")
def sentiment_endpoint(
    comments: str = Query("This film looks amazing!"),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Run sentiment analysis on comma-separated comments.
    Primary: HuggingFace BERT (distilbert). Fallback: ComplementNB + TF-IDF.
    Returns: hype_score, sentiment_label, positive/neutral/negative %, top_keywords.
    """
    comment_list = [c.strip() for c in comments.split(",") if c.strip()]
    result = compute_sentiment(comment_list)
    return result


class BatchSentimentRequest(BaseModel):
    comments: List[str]
    film_id: Optional[str] = None


@router.post("/sentiment-batch")
def sentiment_batch(
    req: BatchSentimentRequest,
    current_user: User = Depends(require_producer_or_admin),
):
    """
    [PRODUCER / ADMIN] Batch sentiment analysis for up to 500 comments.
    Returns per-comment scores + aggregated hype score.
    """
    if len(req.comments) > 500:
        req.comments = req.comments[:500]
    result = compute_sentiment(req.comments)
    result["requested_by"] = current_user.email
    result["film_id"]      = req.film_id or ""
    result["comment_count"] = len(req.comments)
    return result
