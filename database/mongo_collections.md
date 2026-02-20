# MongoDB Collection Design — FilmPulse AI

## Overview
MongoDB stores unstructured/semi-structured data that doesn't fit relational tables.

---

## Collection: `trailer_analysis`

```json
{
  "_id": "ObjectId",
  "film_id": "FP-XXXXXXXX",
  "filename": "trailer.mp4",
  "analyzed_at": "ISO8601",
  "viral_potential": 84,
  "engagement_score": 76,
  "emotional_peak": 92,
  "emotional_curve": [10, 22, 45, 72, 92, 65, 38],
  "scene_intensity": [42, 65, 80, 93, 55],
  "insights": ["Strong opening hook", "High meme potential at 45s"],
  "frames_processed": 3600,
  "model_version": "CNN-EmotionNet-v2"
}
```

---

## Collection: `social_comments`

```json
{
  "_id": "ObjectId",
  "film_id": "FP-XXXXXXXX",
  "platform": "Twitter",
  "username": "@user123",
  "text": "This film looks incredible!",
  "sentiment": "positive",
  "sentiment_score": 0.94,
  "likes": 142,
  "retweets": 38,
  "collected_at": "ISO8601"
}
```

---

## Collection: `sentiment_data`

```json
{
  "_id": "ObjectId",
  "film_id": "FP-XXXXXXXX",
  "snapshot_time": "ISO8601",
  "hype_score": 78,
  "positive_count": 1240,
  "neutral_count": 340,
  "negative_count": 120,
  "trending_keywords": ["blockbuster", "epic", "must-watch"],
  "platform_breakdown": {
    "Twitter": {"positive": 700, "neutral": 180, "negative": 90},
    "Instagram": {"positive": 540, "neutral": 160, "negative": 30}
  }
}
```

---

## Collection: `trend_history`

```json
{
  "_id": "ObjectId",
  "film_id": "FP-XXXXXXXX",
  "recorded_at": "ISO8601",
  "google_trends_score": 72,
  "youtube_views_24h": 1450000,
  "twitter_mentions_24h": 38400,
  "instagram_tags_24h": 12800,
  "region_trends": {
    "Mumbai": 88,
    "Delhi": 76,
    "Bangalore": 65
  }
}
```

---

## Indexes
- `social_comments`: `film_id`, `platform`, `sentiment`
- `trend_history`: `film_id`, `recorded_at` (TTL 90 days)
- `trailer_analysis`: `film_id` (unique)
