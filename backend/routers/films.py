"""
FilmPulse AI — Films Router (with real SQLAlchemy persistence)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from database import get_db, Film, User
from auth import get_current_user, require_user, require_producer_or_admin
from ml.audience_model import predict_audience
from ml.discoverability import auto_compute_discoverability
from ml.sentiment_engine import compute_sentiment
import uuid

router = APIRouter()


class FilmUpload(BaseModel):
    title: str
    genre: str
    language: str
    budget: float
    release_date: str
    platform: str
    cast_popularity: Optional[float] = 7.0
    director: Optional[str] = None
    production_house: Optional[str] = None


class FilmResponse(BaseModel):
    film_id: str
    title: str
    status: str
    message: str
    created_at: str
    discoverability: Optional[float] = None
    hype_score: Optional[float] = None
    revenue_estimate: Optional[float] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    budget: Optional[float] = None
    platform: Optional[str] = None
    director: Optional[str] = None


@router.post("/upload-film", response_model=FilmResponse, status_code=201)
def upload_film(
    film: FilmUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_producer_or_admin),
):
    """Upload film metadata, run AI analysis, and persist to database."""
    film_id = str(uuid.uuid4())[:8].upper()

    # Parse release month for timing score
    try:
        release_month = int(film.release_date.split("-")[1]) if film.release_date else 6
    except Exception:
        release_month = 6

    # Run enriched ML pipeline
    audience = predict_audience(
        genre=film.genre,
        budget=film.budget,
        language=film.language,
        trailer_sentiment=0.72,
        cast_popularity=film.cast_popularity or 7.0,
    )
    discovery = auto_compute_discoverability(
        genre=film.genre,
        budget=film.budget,
        language=film.language,
        cast_popularity=film.cast_popularity or 7.0,
        trailer_sentiment=0.72,
        release_month=release_month,
        genre_score=audience["genre_score"],
    )
    sentiment = compute_sentiment(["This film looks exciting and promising"])
    hype = sentiment["hype_score"]
    rev_mid = audience["revenue_estimate"]["mid"]

    # Persist to DB
    db_film = Film(
        film_id=film_id,
        title=film.title,
        genre=film.genre,
        language=film.language,
        budget=film.budget,
        release_date=film.release_date,
        platform=film.platform,
        director=film.director,
        production_house=film.production_house,
        cast_popularity=film.cast_popularity or 7.0,
        discoverability=discovery["score"],
        hype_score=float(hype),
        revenue_estimate=rev_mid,
        grade=discovery["grade"],
        status="analyzed",
        owner_id=current_user.id if current_user else None,
        created_at=datetime.utcnow(),
    )
    db.add(db_film)
    db.commit()
    db.refresh(db_film)

    return FilmResponse(
        film_id=film_id,
        title=film.title,
        status="analyzed",
        message=f"Film '{film.title}' registered and analyzed successfully!",
        created_at=db_film.created_at.isoformat(),
        discoverability=discovery["score"],
        hype_score=float(hype),
        revenue_estimate=rev_mid,
        genre=film.genre,
        language=film.language,
        budget=film.budget,
        platform=film.platform,
        director=film.director,
    )


@router.get("/films")
def list_films(
    show_all: bool = False,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Return films for the authenticated user. Admins can pass show_all=true."""
    if current_user and (current_user.role == "admin") and show_all:
        films = db.query(Film).order_by(Film.created_at.desc()).all()
    elif current_user:
        films = db.query(Film).filter(Film.owner_id == current_user.id).order_by(Film.created_at.desc()).all()
    else:
        # Public: return recent 20 films (no sensitive data)
        films = db.query(Film).order_by(Film.created_at.desc()).limit(20).all()

    return {
        "films": [
            {
                "film_id": f.film_id,
                "title": f.title,
                "genre": f.genre,
                "language": f.language,
                "budget": f.budget,
                "platform": f.platform,
                "director": f.director,
                "release_date": f.release_date,
                "discoverability": f.discoverability,
                "hype_score": f.hype_score,
                "revenue_estimate": f.revenue_estimate,
                "status": f.status,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in films
        ]
    }


@router.get("/films/{film_id}")
def get_film(film_id: str, db: Session = Depends(get_db)):
    """Retrieve film details by ID."""
    film = db.query(Film).filter(Film.film_id == film_id).first()
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    return {
        "film_id": film.film_id,
        "title": film.title,
        "genre": film.genre,
        "language": film.language,
        "budget": film.budget,
        "platform": film.platform,
        "director": film.director,
        "release_date": film.release_date,
        "discoverability": film.discoverability,
        "hype_score": film.hype_score,
        "revenue_estimate": film.revenue_estimate,
        "status": film.status,
        "created_at": film.created_at.isoformat() if film.created_at else None,
    }


@router.delete("/films/{film_id}")
def delete_film(
    film_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """Delete a film by ID. Producers can only delete their own. Admins can delete any."""
    film = db.query(Film).filter(Film.film_id == film_id).first()
    if not film:
        raise HTTPException(status_code=404, detail="Film not found")
    # Admins bypass ownership check
    if current_user.role != "admin" and film.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You don't own this film")
    db.delete(film)
    db.commit()
    return {"message": f"Film '{film.title}' deleted successfully"}
