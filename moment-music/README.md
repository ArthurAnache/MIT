# Moment Music (Block 5) — Google Trends → Topics → MusicGen Prompts

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open:
- `GET http://127.0.0.1:8000/trends?geo=FR&limit=10`
- `POST http://127.0.0.1:8000/trends/select`

## Example: GET /trends

```json
{
  "geo": "FR",
  "limit": 10,
  "fetched_at": "2026-02-07T19:35:10.123Z",
  "cache_hit": false,
  "candidates": [
    {
      "topic_id": "a1b2c3d4e5f6a7b8",
      "title": "Example trending topic",
      "source": "google_trends_rss",
      "timestamp": "2026-02-07T00:00:00Z",
      "score": 1.15,
      "raw": {"link": "..."},
      "flags": ["interest:tech:1"]
    }
  ],
  "suggested_selection": ["a1b2c3d4e5f6a7b8", "..."]
}
```

## Example: POST /trends/select

Request:
```json
{
  "geo": "FR",
  "mode": "auto",
  "limit": 10,
  "select_k": 5,
  "user_profile": {
    "user_id": "abc",
    "interests": ["tech", "sports", "finance"],
    "avoid": ["politics", "crime"],
    "default_genre": "electronic pop",
    "default_vibe": "uplifting, high energy, modern",
    "preferred_instruments": ["synth", "drums"],
    "language": "fr"
  },
  "use_llm": false
}
```

Response (extract):
```json
{
  "geo": "FR",
  "selected_topics": [
    {"topic_id": "...", "title": "...", "score": 1.2, "flags": []}
  ],
  "prompts": [
    {
      "topic_id": "...",
      "topic_title": "...",
      "prompt_template": "electronic pop, uplifting... Theme inspired by: ...",
      "prompt_llm": null
    }
  ],
  "block2_contract": {
    "knowledge_vector": "Trend: ... | Prompt: ...\nTrend: ... | Prompt: ...",
    "trend_context": ["..."],
    "user_profile": {"...": "..."},
    "creative_state_patch": {
      "intent_additions": ["..."],
      "style_additions": ["electronic pop", "uplifting, high energy, modern"],
      "decisions_patch": {"trend_topics": ["..."], "trend_selected_at": "..."}
    }
  }
}
```

## Notes
- Default source is **Google Trends RSS** (no credentials).
- Optional pytrends fallback: set `TRENDS_USE_PYTRENDS_FALLBACK=1`.
- Trends are cached for 15 minutes per geo (`TRENDS_CACHE_TTL_SECONDS`).
