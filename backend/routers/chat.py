"""
FilmPulse AI Chatbot — LLM-Powered Conversational Intelligence
-------------------------------------------------------------
Uses Google Gemini 1.5 Flash as the core engine.
Injects:
1. System Instruction (Industry Knowledge & FilmPulse Platform features)
2. User Context (Current films owned by the user)
3. Chat History (Last 10 turns)
"""
import os
import random
from datetime import datetime
from typing import List, Optional

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import ChatMessage, Film, get_db
from auth import User, get_current_user

router = APIRouter()

# ── 1. AGENT CONFIGURATION ──────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# System Instruction: This grounds the AI in the FilmPulse domain
SYSTEM_INSTRUCTION = """
You are 'FilmPulse AI', an advanced conversational assistant for Indian film producers. 
Your goal is to provide data-driven, strategic advice for film production and marketing.

Core Knowledge Base:
- Audience Prediction: Uses XGBoost on TMDB/IMDb data. Accuracy ~89%. Predicts age, gender, revenue.
- Budget Optimization: Uses Ridge Regression to allocate spend across YouTube, Instagram, TV, etc.
- Trailer Analyzer: CNN-based pipeline for emotional curves and viral potential scores.
- Discoverability Score: Composite metric (0-100) from Audience Match, Buzz, Competition, Budget, and Timing.
  - Grade A (80+): Wide theatrical.
  - Grade B (65+): OTT + selective theatrical.
- Hype Score (0-100): Calculated from BERT-based sentiment analysis of social feeds.

Style Guidelines:
- Be professional yet supportive. 
- Use markdown (bold, bullet points) for readability.
- When answering broad industry questions, relate them back to how FilmPulse AI features can help.
- If you don't know something specifically related to the user's private data, stick to the platform's features.
- Keep responses concise (under 250 words unless asked for technical breakdown).
"""

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_INSTRUCTION
        )
    except Exception as e:
        print(f"FAILED TO INITIALIZE GEMINI: {e}")
        model = None
else:
    model = None


# ── 2. MODELS ────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = None
    film_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    intent: str
    suggested_actions: Optional[List[str]] = None


# ── 3. CORE LOGIC ────────────────────────────────────────────────────────────

def _get_user_context(db: Session, user_id: int) -> str:
    """Inject current film data to make the AI aware of user's projects."""
    films = db.query(Film).filter(Film.owner_id == user_id).all()
    if not films:
        return "The user has not registered any films yet."
    
    context = "Here are the films currently managed by the user:\n"
    for f in films:
        context += f"- {f.title} (Genre: {f.genre}, Status: {f.status}, Discoverability: {f.discoverability or 'N/A'})\n"
    return context

def _get_chat_history(db: Session, user_id: int, limit: int = 10) -> List[dict]:
    """Retrieve recent history in Gemini format."""
    msgs = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).order_by(ChatMessage.created_at.desc()).limit(limit).all()
    history = []
    for m in reversed(msgs):
        history.append({
            "role": "user" if m.role == "user" else "model",
            "parts": [m.content]
        })
    return history

# ── 4. ENDPOINTS ─────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Conversational endpoint with LLM fallback and context injection."""
    user_msg = req.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Empty message")

    # If no API key, use 
    if not model:
        return ChatResponse(
            reply="⚠️ **FilmPulse AI is in 'Offline Mode' (No API Key).**\n\nPlease add a `GEMINI_API_KEY` to your `backend/.env` file to enable the real AI chatbot. \n\nI can still answer basic questions about the platform, but my 'intelligence' is currently limited.",
            intent="offline_fallback"
        )

    try:
        # Prepare Context
        user_context = _get_user_context(db, current_user.id)
        chat_history = _get_chat_history(db, current_user.id)

        # Build prompt with context
        prefix = f"[SYSTEM: User Context]\n{user_context}\n\n"
        
        chat_session = model.start_chat(history=chat_history)
        response = chat_session.send_message(f"{prefix}[USER]: {user_msg}")
        
        ai_reply = response.text

        # Persist to DB
        db.add(ChatMessage(user_id=current_user.id, role="user", content=user_msg))
        db.add(ChatMessage(user_id=current_user.id, role="assistant", content=ai_reply))
        db.commit()

        return ChatResponse(
            reply=ai_reply,
            intent="llm_generated",
            suggested_actions=["Analyze Trailer", "Check Discoverability"] if "trailer" in user_msg.lower() or "marketing" in user_msg.lower() else None
        )

    except Exception as e:
        db.rollback()
        print(f"Chat Error: {str(e)}")
        return ChatResponse(
            reply="I'm having a bit of trouble connecting to my creative centers. Please try again in 30 seconds!",
            intent="error"
        )

@router.get("/chat/history")
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch user's chat history."""
    messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.created_at.asc()).limit(50).all()
    
    return {
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in messages
        ]
    }
