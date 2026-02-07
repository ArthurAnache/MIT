"""Pydantic models and data contracts for Block 5 (Google Trends -> prompts).

These contracts are designed to integrate with the rest of the MVP:
- Block 2 consumes a "knowledge_vector" and related context.
- CreativeState is versioned elsewhere; Block 5 outputs a patch.

All comments are in English by request.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """Minimal user profile used for personalization."""

    user_id: str = Field(..., description="Unique user identifier.")
    interests: List[str] = Field(default_factory=list, description="Interest tags (e.g., tech, sports).")
    avoid: List[str] = Field(default_factory=list, description="Avoid tags (e.g., politics, crime).")
    default_genre: str = Field(default="electronic pop", description="Default genre for prompt building.")
    default_vibe: str = Field(default="uplifting, high energy, modern", description="Default vibe adjectives.")
    preferred_instruments: List[str] = Field(default_factory=lambda: ["synth", "drums"])
    language: str = Field(default="fr", description="User UI language, not necessarily prompt language.")


class TrendTopic(BaseModel):
    """A single trending topic candidate."""

    topic_id: str = Field(..., description="Stable identifier (hash) within a geo/time window.")
    title: str
    source: str = Field(..., description="Source provider (e.g., google_trends_rss).")
    timestamp: datetime = Field(..., description="When the trend item was published/observed.")
    score: float = Field(..., description="Personalized score used for ranking.")
    raw: Dict[str, Any] = Field(default_factory=dict, description="Raw fields from upstream feed, if any.")
    flags: List[str] = Field(default_factory=list, description="Safety/policy flags (e.g., avoid_keyword).")


SelectionMode = Literal["manual", "auto"]


class TrendsQueryResponse(BaseModel):
    """Response for GET /trends."""

    geo: str
    limit: int
    fetched_at: datetime
    cache_hit: bool
    candidates: List[TrendTopic]
    suggested_selection: List[str] = Field(
        default_factory=list,
        description="List of topic_id suggested for selection (auto top-K).",
    )


class TrendSelectionRequest(BaseModel):
    """Request for POST /trends/select."""

    geo: str = "FR"
    mode: SelectionMode = "auto"
    limit: int = 10
    select_k: int = 5
    selected_topic_ids: Optional[List[str]] = None
    user_profile: UserProfile
    use_llm: bool = False


class PromptBundle(BaseModel):
    """Prompts returned for each selected topic."""

    topic_id: str
    topic_title: str
    prompt_template: str
    prompt_llm: Optional[str] = None


class CreativeState(BaseModel):
    """Simplified CreativeState for MVP integration.

    In the full system this would be versioned and contain richer nested structures.
    """

    intent: str = ""
    emotion_curve: str = ""
    style: str = ""
    structure: str = ""
    constraints: Dict[str, Any] = Field(default_factory=dict)
    assets: List[Dict[str, Any]] = Field(default_factory=list)
    decisions: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)


class CreativeStatePatch(BaseModel):
    """Partial update produced by Block 5."""

    intent_additions: List[str] = Field(default_factory=list)
    style_additions: List[str] = Field(default_factory=list)
    decisions_patch: Dict[str, Any] = Field(default_factory=dict)


class Block2Contract(BaseModel):
    """Example contract that Block 2 would receive."""

    knowledge_vector: str
    trend_context: List[TrendTopic]
    user_profile: UserProfile
    creative_state_patch: CreativeStatePatch


class TrendSelectionResponse(BaseModel):
    """Response for POST /trends/select."""

    geo: str
    selected_topics: List[TrendTopic]
    prompts: List[PromptBundle]
    block2_contract: Block2Contract
