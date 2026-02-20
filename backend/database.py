"""
FilmPulse AI — Database Layer (Phase 2)
---------------------------------------
• PostgreSQL (via SQLAlchemy) → Films, Audience, Campaigns, Users, Chat
• SQLite fallback when DATABASE_URL is not set (dev mode)
• MongoDB (via PyMongo) → Trailer Analysis, Social Comments, Sentiment, Trends
"""

from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String, Float,
    Numeric, Text, DateTime, Boolean, ForeignKey, Date, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

# ── PostgreSQL / SQLite connection ────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./filmpulse.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── 1. USERS ─────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    email            = Column(String(200), unique=True, index=True, nullable=False)
    name             = Column(String(100), nullable=False)
    hashed_password  = Column(String(300), nullable=False)
    company          = Column(String(100), nullable=True)
    role             = Column(String(20), default="producer")
    avatar_initials  = Column(String(3), nullable=True)
    is_active        = Column(Boolean, default=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    films            = relationship("Film", back_populates="owner")
    chat_sessions    = relationship("ChatMessage", back_populates="user")


# ── 2. FILMS ─────────────────────────────────────────────────────────────────
class Film(Base):
    __tablename__ = "films"

    id               = Column(Integer, primary_key=True, index=True)
    film_id          = Column(String(20), unique=True, index=True)     # "FP-001234"
    title            = Column(String(200), nullable=False)
    genre            = Column(String(50))
    language         = Column(String(50))
    budget           = Column(Float)                                   # production budget (INR)
    release_date     = Column(String(20))
    platform         = Column(String(50))                              # Theatre | OTT | Both

    # Performance metrics
    box_office       = Column(Float, nullable=True)                    # actual box-office (INR)
    ott_views        = Column(BigInteger, nullable=True)               # OTT streams

    # ML-derived scores
    discoverability  = Column(Float, nullable=True)                    # 0-100
    hype_score       = Column(Float, nullable=True)                    # 0-100
    revenue_estimate = Column(Float, nullable=True)                    # ML mid-point (INR M)
    grade            = Column(String(2), nullable=True)                # A | B | C | D

    # Extended metadata
    director         = Column(String(100), nullable=True)
    production_house = Column(String(100), nullable=True)
    cast_popularity  = Column(Float, default=7.0)                      # 1-10
    trailer_url      = Column(Text, nullable=True)
    poster_url       = Column(Text, nullable=True)
    status           = Column(String(20), default="registered")        # registered|analyzed|released

    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner_id         = Column(Integer, ForeignKey("users.id"), nullable=True)

    # relationships
    owner            = relationship("User", back_populates="films")
    audience_segments= relationship("AudienceSegment", back_populates="film", cascade="all, delete-orphan")
    campaigns        = relationship("Campaign", back_populates="film", cascade="all, delete-orphan")


# ── 3. AUDIENCE SEGMENTS ─────────────────────────────────────────────────────
class AudienceSegment(Base):
    __tablename__ = "audience_segments"

    id               = Column(Integer, primary_key=True, index=True)
    film_id          = Column(Integer, ForeignKey("films.id", ondelete="CASCADE"))

    # Demographics
    age_group        = Column(String(20))           # '18-24'|'25-34'|'35-44'|'45+'
    gender           = Column(String(10))           # 'male'|'female'|'all'
    region           = Column(String(50))           # 'North India'|'Metro Cities'|...
    tier             = Column(String(20))           # 'Tier 1'|'Tier 2'|'Tier 3'

    # Interest profile (stored as JSON string for SQLite compat)
    interest_tags    = Column(Text)                 # JSON list: ["action","thriller"]

    # Predicted engagement
    engagement_score = Column(Float)                # 0-100
    reach_pct        = Column(Float)                # % of segment reachable
    affinity_score   = Column(Float)                # 0-100 genre-audience affinity

    source           = Column(String(30), default="ml_model")
    created_at       = Column(DateTime, default=datetime.utcnow)

    film             = relationship("Film", back_populates="audience_segments")


# ── 4. CAMPAIGNS ─────────────────────────────────────────────────────────────
class Campaign(Base):
    __tablename__ = "campaigns"

    id               = Column(Integer, primary_key=True, index=True)
    film_id          = Column(Integer, ForeignKey("films.id", ondelete="CASCADE"))

    # Channel
    platform         = Column(String(50))           # 'YouTube Ads'|'Instagram'|...
    campaign_name    = Column(String(200), nullable=True)

    # Budget & Performance
    budget           = Column(Float)                # allocated budget (INR)
    actual_spend     = Column(Float, nullable=True) # actual amount spent
    roi              = Column(Float, nullable=True) # return on investment (x)
    impressions      = Column(BigInteger, nullable=True)
    clicks           = Column(Integer, nullable=True)
    conversions      = Column(Integer, nullable=True)
    cpm              = Column(Float, nullable=True)  # cost per 1000 impressions
    ctr              = Column(Float, nullable=True)  # click-through rate

    # Timeline
    spend_date       = Column(String(20), nullable=True)
    start_date       = Column(String(20), nullable=True)
    end_date         = Column(String(20), nullable=True)

    # AI recommendation
    ai_recommended   = Column(Boolean, default=False)
    allocation_pct   = Column(Float, nullable=True) # % of total budget by ML

    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    film             = relationship("Film", back_populates="campaigns")


# ── 5. CHAT MESSAGES ─────────────────────────────────────────────────────────
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    role       = Column(String(10))    # "user" | "assistant"
    content    = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user       = relationship("User", back_populates="chat_sessions")


# ── DB Helpers ────────────────────────────────────────────────────────────────
def init_db():
    """Create all SQLAlchemy tables (used on FastAPI startup)."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yield a DB session, close on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
