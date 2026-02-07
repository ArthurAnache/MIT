"""Scoring + safety filtering for trending topics.

We start from a base rank-derived score, then apply personalization:
- Boost if topic matches user's interests (keyword heuristics)
- Downrank/remove if matches avoid list or safety keywords

This is a hackathon MVP: keep it deterministic and explainable.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Tuple

from .models import TrendTopic, UserProfile

logger = logging.getLogger(__name__)

# Very simple keyword banks for common interest tags.
INTEREST_KEYWORDS: Dict[str, List[str]] = {
    "tech": ["ai", "openai", "deepseek", "gpu", "nvidia", "apple", "iphone", "android", "tesla", "robot", "startup"],
    "sports": ["match", "league", "champions", "football", "soccer", "nba", "tennis", "rugby", "olympics"],
    "finance": ["stocks", "market", "bitcoin", "crypto", "rate", "inflation", "earnings", "ipo", "bank"],
    "music": ["album", "song", "festival", "concert", "tour", "grammy", "dj"],
    "movies": ["film", "trailer", "netflix", "cinema", "series"],
}

DEFAULT_AVOID_KEYWORDS: Dict[str, List[str]] = {
    "politics": ["election", "president", "parliament", "government", "minister", "senate", "politic"],
    "violence": ["shooting", "killed", "attack", "war", "terror", "bomb", "massacre"],
    "crime": ["murder", "arrest", "trial", "police", "fraud", "robbery"],
}


def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _keyword_hits(title: str, keywords: List[str]) -> int:
    t = normalize_text(title)
    return sum(1 for kw in keywords if kw.lower() in t)


def score_and_filter(
    raw_items: List[dict],
    user: UserProfile,
    remove_hard_blocks: bool = True,
) -> List[TrendTopic]:
    """Convert raw items -> TrendTopic with scores and flags.

    Args:
        raw_items: List of raw dict items produced by the fetcher.
        user: UserProfile used for personalization.
        remove_hard_blocks: If True, hard-blocked items are removed.

    Returns:
        Sorted list of TrendTopic by score desc.
    """
    avoid_tags = [a.lower() for a in (user.avoid or [])]

    # Build avoid keyword list (tags -> keywords) + literal tag words.
    avoid_keywords: List[str] = []
    for tag in avoid_tags:
        avoid_keywords += DEFAULT_AVOID_KEYWORDS.get(tag, [])
        avoid_keywords.append(tag)

    scored: List[Tuple[float, TrendTopic]] = []

    for idx, item in enumerate(raw_items):
        title = item.get("title", "")
        flags: List[str] = []

        # Base score: higher for top-ranked items.
        base = max(0.0, 1.0 - (idx / max(1, len(raw_items))))  # 1.0 .. ~0
        score = base

        # Interest boosts.
        for interest in (user.interests or []):
            kws = INTEREST_KEYWORDS.get(interest.lower())
            if not kws:
                # If interest is unknown, use it as a literal keyword.
                hits = _keyword_hits(title, [interest])
            else:
                hits = _keyword_hits(title, kws)
            if hits:
                score += 0.15 * hits
                flags.append(f"interest:{interest.lower()}:{hits}")

        # Avoid / safety downranking.
        avoid_hits = _keyword_hits(title, avoid_keywords)
        if avoid_hits:
            score -= 0.6 * avoid_hits
            flags.append(f"avoid:{avoid_hits}")

        # Generic mild safety: downrank if contains very sensitive words
        generic_sensitive = _keyword_hits(title, DEFAULT_AVOID_KEYWORDS["violence"] + DEFAULT_AVOID_KEYWORDS["crime"])
        if generic_sensitive:
            score -= 0.25 * generic_sensitive
            flags.append(f"sensitive:{generic_sensitive}")

        hard_block = False
        if remove_hard_blocks and avoid_hits >= 2:
            # If the user wants to avoid something and it strongly matches, drop it.
            hard_block = True
            flags.append("hard_block")

        topic = TrendTopic(
            topic_id=item["topic_id"],
            title=title,
            source=item.get("source", "unknown"),
            timestamp=item.get("timestamp"),
            score=float(score),
            raw=item.get("raw", {}),
            flags=flags,
        )

        if hard_block:
            logger.info("Dropping hard-blocked trend", extra={"title": title, "flags": flags})
            continue

        scored.append((topic.score, topic))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored]
