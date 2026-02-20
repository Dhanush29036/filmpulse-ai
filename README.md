# FilmPulse AI

> **Turning Creative Vision into Data-Driven Success**

AI-powered decision intelligence platform for film producers — predicts audience demand, optimizes marketing budget, analyzes trailers, and tracks buzz in real time.

---

## 🚀 Quick Start

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000
# → Docs: http://localhost:8000/docs
```

---

## 📁 Project Structure

```
kp/
├── frontend/                  # React + Vite SPA
│   └── src/
│       ├── pages/
│       │   ├── LandingPage.jsx
│       │   ├── Dashboard.jsx
│       │   ├── TrailerAnalysis.jsx
│       │   ├── CampaignOptimizer.jsx
│       │   └── SentimentMonitor.jsx
│       └── components/
│           └── Navbar.jsx
├── backend/                   # FastAPI
│   ├── main.py
│   ├── database.py            # SQLAlchemy ORM
│   ├── routers/
│   │   ├── films.py
│   │   ├── analysis.py
│   │   ├── optimization.py
│   │   └── dashboard.py
│   └── ml/
│       ├── audience_model.py  # XGBoost stub
│       ├── sentiment_engine.py# BERT stub
│       ├── budget_optimizer.py# Linear regression stub
│       └── discoverability.py # Signature score formula
├── database/
│   ├── schema.sql             # PostgreSQL DDL
│   └── mongo_collections.md   # MongoDB design doc
└── docker-compose.yml
```

---

## 🧠 AI Modules

| Module | Algorithm | Output |
|---|---|---|
| Audience Prediction | XGBoost | Age group, region, revenue range |
| Trailer Analyzer | CNN + OpenCV | Emotional curve, viral potential |
| Sentiment Engine | BERT (HuggingFace) | Hype Score 0-100 |
| Budget Optimizer | Linear Regression | Channel allocation + ROI |
| Discoverability Score | Weighted formula | Composite 0-100 score |

---

## 🔌 API Endpoints

```
POST /api/v1/upload-film
POST /api/v1/analyze-trailer
GET  /api/v1/predict-audience
GET  /api/v1/sentiment-analysis
GET  /api/v1/budget-optimization
GET  /api/v1/release-recommendation
GET  /api/v1/dashboard-summary
```

---

## 🗄️ Database Configuration

Set environment variable:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/filmpulse
MONGO_URL=mongodb://localhost:27017/filmpulse
```

Default (no config needed): SQLite (`filmpulse.db` file)

---

## 🐳 Docker

```bash
docker-compose up -d
```
