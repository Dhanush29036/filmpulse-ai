from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import films, analysis, optimization, dashboard, chat
from routers.auth_router import router as auth_router
from routers.trends   import router as trends_router
from routers.advanced import router as advanced_router
from database import init_db
from mongo_db import init_mongo
from realtime_collector import start_scheduler, stop_scheduler
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize PostgreSQL + MongoDB + APScheduler cron on startup."""
    init_db()        # SQLAlchemy → create all PostgreSQL/SQLite tables
    init_mongo()     # PyMongo   → ensure collections + indexes exist
    start_scheduler()  # APScheduler → hourly real-time data collection
    yield
    stop_scheduler()   # Graceful shutdown


app = FastAPI(
    title="FilmPulse AI API",
    description="AI-powered decision intelligence platform for film producers",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(auth_router,          prefix="/api/v1", tags=["Auth"])
app.include_router(films.router,         prefix="/api/v1", tags=["Films"])
app.include_router(analysis.router,      prefix="/api/v1", tags=["Analysis"])
app.include_router(optimization.router,  prefix="/api/v1", tags=["Optimization"])
app.include_router(dashboard.router,     prefix="/api/v1", tags=["Dashboard"])
app.include_router(trends_router,        prefix="/api/v1", tags=["Real-Time Trends"])
app.include_router(advanced_router,      prefix="/api/v1", tags=["Advanced AI"])
app.include_router(chat.router,          prefix="/api/v1", tags=["Chat"])


@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "service": "FilmPulse AI", "version": "3.0.0",
            "phases": ["ML", "Auth/RBAC", "RealTime", "Deployed"]}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
