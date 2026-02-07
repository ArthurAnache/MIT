from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from trends.fetcher import fetch_trends
from trends.models import UserProfile
from trends.prompt_builder import build_prompts
import json
import ssl
import time
import urllib.parse
import urllib.request
import certifi

_MB_CACHE: dict[str, bool] = {}


@dataclass
class TrendItem:
    topic_id: str
    title: str
    source: str = "google_trends_rss"
    timestamp: Optional[str] = None
    score: float = 0.0
    raw: Dict[str, Any] = field(default_factory=dict)
    flags: List[str] = field(default_factory=list)


def _to_trend_item(d: Dict[str, Any]) -> TrendItem:
    return TrendItem(
        topic_id=str(d.get("topic_id", "")),
        title=str(d.get("title", "")),
        source=str(d.get("source", "google_trends_rss")),
        timestamp=(d.get("timestamp") if isinstance(d.get("timestamp"), str) else None),
        score=float(d.get("score", 0.0) or 0.0),
        raw=dict(d.get("raw", {}) or {}),
        flags=list(d.get("flags", []) or []),
    )


def _looks_like_match_or_sports(title: str) -> bool:
    t = title.lower()
    # very common patterns for sports fixtures / matchups
    if " vs " in t or " v " in t:
        return True
    if " - " in t and any(k in t for k in [" vs", " v "]):
        return True
    # also catch things like "team - team" often used for fixtures
    if " - " in t and len(t.split(" - ")) == 2:
        return True
    # common sports tokens (optional, but helps)
    sports_tokens = ["fc", "cf", "vs", "league", "nba", "nfl", "ufc", "bkfc"]
    if any(tok in t.split() for tok in sports_tokens):
        return True
    return False


def is_music_artist_musicbrainz(name: str, min_score: int = 80) -> bool:
    """Verify if a trend keyword is a musical artist using MusicBrainz (no API key)."""
    key = name.strip().lower()
    if not key:
        return False
    if key in _MB_CACHE:
        return _MB_CACHE[key]

    if _looks_like_match_or_sports(name):
        _MB_CACHE[key] = False
        return False

    # Build MusicBrainz query
    q = f'artist:"{name}"'
    params = urllib.parse.urlencode({"query": q, "fmt": "json", "limit": "1"})
    url = f"https://musicbrainz.org/ws/2/artist?{params}"

    headers = {
        # MusicBrainz requires a proper User-Agent; put your project name/email.
        "User-Agent": "moment-music-hackathon/0.1 (contact: louis@example.com)",
        "Accept": "application/json",
    }

    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        _MB_CACHE[key] = False
        return False

    artists = data.get("artists") or []
    if not artists:
        _MB_CACHE[key] = False
        return False

    a0 = artists[0]
    score = int(a0.get("score") or 0)
    a_type = (a0.get("type") or "").lower()  # "Person", "Group", etc.

    ok_type = a_type in {"person", "group", "orchestra", "choir"}
    ok = (score >= min_score) and ok_type

    _MB_CACHE[key] = ok

    # Be nice with rate-limiting (MusicBrainz asks for polite usage)
    time.sleep(0.2)

    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Get top musical artist trend + MusicGen prompt.")
    parser.add_argument("--geo", default="US", help="Country code (US, FR, etc.)")
    parser.add_argument("--limit", type=int, default=10, help="Number of trends to fetch")
    args = parser.parse_args()

    raw_trends = fetch_trends(args.geo, limit=args.limit)

    # Convert dicts -> minimal TrendItem
    items = [_to_trend_item(d) for d in raw_trends]

    # find first likely artist
    artist_trend = None
    artist_trend = None
    for item in items:
        if is_music_artist_musicbrainz(item.title):
            artist_trend = item
            break


    if not artist_trend:
        print("No music artist found in top trends right now.")
    else:
        print(artist_trend.title)


    # build a prompt for this single artist
    # wrap the trend into a list so build_prompts works
    single_list = [artist_trend]
    profile = UserProfile(
        user_id="global",
        interests=[],
        avoid=[],
        default_genre="pop",
        default_vibe="modern, radio-ready",
        preferred_instruments=["synth", "guitar"],
        language="en",
    )

    prompts = build_prompts(single_list, profile, use_llm=False)

    print("=== Worldwide Top Musical Trend ===")
    print("Artist/Trend:", artist_trend.title)
    print("\n=== MusicGen Prompt ===")
    for p in prompts:
        print(p.prompt_template)


if __name__ == "__main__":
    main()
