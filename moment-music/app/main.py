"""FastAPI app exposing Block 5 endpoints.

Run:
  uvicorn app.main:app --reload --port 8000

Endpoints:
  GET  /trends?geo=FR&limit=10
  POST /trends/select

No external services required (RSS is default).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query

from trends.cache import TTLCache
from trends.fetcher import fetch_trends
from trends.models import (
    Block2Contract,
    CreativeStatePatch,
    TrendSelectionRequest,
    TrendSelectionResponse,
    TrendsQueryResponse,
    TrendTopic,
    UserProfile,
)
from trends.prompt_builder import build_knowledge_vector, build_prompts
from trends.scoring import score_and_filter

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("moment_music")

app = FastAPI(title="Moment Music - Block 5", version="0.1.0")

CACHE_TTL_SECONDS = int(os.getenv("TRENDS_CACHE_TTL_SECONDS", str(15 * 60)))
USE_PYTRENDS_FALLBACK = os.getenv("TRENDS_USE_PYTRENDS_FALLBACK", "0") == "1"

cache = TTLCache(
    ttl_seconds=CACHE_TTL_SECONDS,
    persist_path=Path(os.getenv("TRENDS_CACHE_PATH", ".cache/trends_cache.json")),
)


def _default_user() -> UserProfile:
    # Lightweight default for GET /trends if no profile is provided.
    return UserProfile(
        user_id="anonymous",
        interests=["tech", "music"],
        avoid=["politics", "crime"],
        default_genre="electronic pop",
        default_vibe="uplifting, high energy, modern",
        preferred_instruments=["synth", "drums"],
        language="fr",
    )


@app.get("/trends", response_model=TrendsQueryResponse)
def get_trends(
    geo: str = Query(default="FR", min_length=2, max_length=2),
    limit: int = Query(default=10, ge=1, le=50),
):
    """Return trend candidates and an auto suggested selection.

    For MVP we score using an anonymous default profile.
    In production you'd pass the real user profile.
    """
    cached, fresh = cache.get(geo.upper())

    raw_items = None
    cache_hit = False

    if fresh and cached:
        raw_items = cached
        cache_hit = True
    else:
        try:
            raw_items = fetch_trends(geo=geo, limit=limit, use_pytrends_fallback=USE_PYTRENDS_FALLBACK)
            cache.set(geo.upper(), raw_items)
            cache_hit = False
        except Exception as e:
            # Fallback to stale cache if present
            if cached:
                raw_items = cached
                cache_hit = True
                logger.warning("Using stale cache due to fetch failure", extra={"geo": geo, "error": str(e)})
            else:
                raise HTTPException(status_code=502, detail=f"Failed to fetch trends: {e}")

    user = _default_user()
    topics = score_and_filter(raw_items[:limit], user)

    # Suggested selection: top 5 topic_ids.
    suggested = [t.topic_id for t in topics[:5]]

    return TrendsQueryResponse(
        geo=geo.upper(),
        limit=limit,
        fetched_at=datetime.now(timezone.utc),
        cache_hit=cache_hit,
        candidates=topics,
        suggested_selection=suggested,
    )


@app.post("/trends/select", response_model=TrendSelectionResponse)
def select_trends(req: TrendSelectionRequest):
    """Accept user selection (manual or auto), return prompts and Block2 contract."""
    geo = req.geo.upper()

    cached, fresh = cache.get(geo)
    raw_items = None

    if fresh and cached:
        raw_items = cached
    else:
        try:
            raw_items = fetch_trends(geo=geo, limit=req.limit, use_pytrends_fallback=USE_PYTRENDS_FALLBACK)
            cache.set(geo, raw_items)
        except Exception as e:
            if cached:
                raw_items = cached
                logger.warning("Using stale cache due to fetch failure", extra={"geo": geo, "error": str(e)})
            else:
                raise HTTPException(status_code=502, detail=f"Failed to fetch trends: {e}")

    candidates = score_and_filter(raw_items[: req.limit], req.user_profile)

    # Determine selection
    if req.mode == "manual":
        if not req.selected_topic_ids:
            raise HTTPException(status_code=400, detail="manual mode requires selected_topic_ids")
        selected_ids = set(req.selected_topic_ids)
        selected = [t for t in candidates if t.topic_id in selected_ids]
    else:
        # Auto: select top K
        k = max(1, min(req.select_k, len(candidates)))
        selected = candidates[:k]
        # Optional override: if user provided IDs, use them instead
        if req.selected_topic_ids:
            selected_ids = set(req.selected_topic_ids)
            selected = [t for t in candidates if t.topic_id in selected_ids]
            if not selected:
                selected = candidates[:k]

    prompts = build_prompts(selected, req.user_profile, use_llm=req.use_llm)
    knowledge_vector = build_knowledge_vector(selected, prompts)

    # CreativeState patch: add thematic keywords to intent/style.
    intent_additions = [t.title for t in selected]
    style_additions = [req.user_profile.default_genre, req.user_profile.default_vibe]
    decisions_patch = {
        "trend_topics": [t.model_dump() for t in selected],
        "trend_selected_at": datetime.now(timezone.utc).isoformat(),
    }

    patch = CreativeStatePatch(
        intent_additions=intent_additions,
        style_additions=style_additions,
        decisions_patch=decisions_patch,
    )

    block2 = Block2Contract(
        knowledge_vector=knowledge_vector,
        trend_context=selected,
        user_profile=req.user_profile,
        creative_state_patch=patch,
    )

    return TrendSelectionResponse(
        geo=geo,
        selected_topics=selected,
        prompts=prompts,
        block2_contract=block2,
    )
