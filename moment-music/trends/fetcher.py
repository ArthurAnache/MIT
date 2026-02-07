"""Fetch trending topics.

Default: Google Trends RSS feeds (Trending RSS first, then Daily/Realtime as legacy fallbacks).
Optional fallback: pytrends (unofficial), behind a feature flag.

Design goals:
- Minimal credentials (RSS requires none)
- Robust error handling
- Pluggable sources
"""

from __future__ import annotations

import hashlib
import logging
import ssl
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List

import certifi
import feedparser

try:
    from dateutil import parser as date_parser
except Exception:  # pragma: no cover
    date_parser = None

logger = logging.getLogger(__name__)

# Most stable public RSS (works for many geos)
RSS_URL_TRENDING = "https://trends.google.com/trending/rss?geo={geo}"

# Legacy endpoints (often 404 depending on Google changes/geo)
RSS_URL_DAILY = "https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo}"
RSS_URL_REALTIME = "https://trends.google.com/trends/trendingsearches/realtime/rss?geo={geo}"

# Some environments get blocked or misclassified without a UA header.
DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


class TrendsFetcherError(RuntimeError):
    pass


def _stable_id(geo: str, title: str, ts: datetime) -> str:
    """Generate a stable ID for a trend item."""
    key = f"{geo}:{title.strip().lower()}:{int(ts.timestamp())}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _fetch_rss_bytes(url: str, timeout_s: int = 10) -> bytes:
    """Fetch RSS bytes with SSL verification (certifi) + User-Agent header."""
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA})
    with urllib.request.urlopen(req, context=ctx, timeout=timeout_s) as response:
        return response.read()


def _parse_entries_to_items(
    geo: str,
    entries: List[Dict[str, Any]],
    limit: int,
    source: str,
    rss_url: str,
) -> List[Dict[str, Any]]:
    """Convert feedparser entries into our raw item dicts."""
    items: List[Dict[str, Any]] = []
    for e in entries[: max(limit, 0)]:
        title = (e.get("title") or "").strip()
        published = e.get("published") or e.get("updated")

        # Parse to datetime
        if published and date_parser:
            try:
                ts = date_parser.parse(published)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                ts = datetime.now(timezone.utc)
        else:
            ts = datetime.now(timezone.utc)

        items.append(
            {
                "topic_id": _stable_id(geo, title, ts),
                "title": title,
                "timestamp": ts.isoformat(),
                "source": source,
                "raw": {
                    "ht_news_item_url": e.get("ht_news_item_url"),
                    "ht_approx_traffic": e.get("ht_approx_traffic"),
                    "link": e.get("link"),
                    "summary": e.get("summary"),
                    "rss_url": rss_url,
                },
            }
        )
    return items


def fetch_from_rss(geo: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch trending searches using Google's public RSS feeds.

    Tries TRENDING first (recommended), then DAILY/REALTIME as legacy fallbacks.

    Notes:
    - Uses certifi CA bundle to fix macOS SSL CERTIFICATE_VERIFY_FAILED in venvs.
    - Adds a User-Agent header to avoid occasional 404/403 blocking.
    - Fetches bytes via urllib, then parses bytes with feedparser.
    """
    geo_up = geo.upper()
    urls = [
        RSS_URL_TRENDING.format(geo=geo_up),
        RSS_URL_DAILY.format(geo=geo_up),
        RSS_URL_REALTIME.format(geo=geo_up),
    ]

    last_exc: Exception | None = None

    for url in urls:
        logger.info("Fetching trends via RSS", extra={"geo": geo, "url": url})
        try:
            data = _fetch_rss_bytes(url, timeout_s=10)
            feed = feedparser.parse(data)

            if getattr(feed, "bozo", False):
                exc = getattr(feed, "bozo_exception", None)
                raise TrendsFetcherError(f"RSS parse error: {exc}")

            entries = getattr(feed, "entries", []) or []
            if not entries:
                raise TrendsFetcherError("RSS feed returned no entries")

            return _parse_entries_to_items(
                geo=geo,
                entries=entries,
                limit=limit,
                source="google_trends_rss",
                rss_url=url,
            )

        except Exception as exc:
            last_exc = exc
            logger.warning(
                "RSS URL failed, trying next",
                extra={"geo": geo, "url": url, "error": str(exc)},
            )

    raise TrendsFetcherError(f"RSS fetch error: {last_exc}")


def fetch_from_pytrends(geo: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Optional fallback using pytrends.

    NOTE: pytrends is unofficial and can break due to Google changes.
    """
    try:
        from pytrends.request import TrendReq
    except Exception as e:  # pragma: no cover
        raise TrendsFetcherError(f"pytrends is not installed/available: {e}")

    logger.warning("Fetching trends via pytrends (unofficial)", extra={"geo": geo})

    pytr = TrendReq(hl="en-US", tz=0)
    # trending_searches returns a DataFrame with 1 column
    df = pytr.trending_searches(pn=geo.upper())
    titles = df.iloc[:limit, 0].astype(str).tolist()

    ts = datetime.now(timezone.utc)
    items: List[Dict[str, Any]] = []
    for t in titles:
        title = t.strip()
        items.append(
            {
                "topic_id": _stable_id(geo, title, ts),
                "title": title,
                "timestamp": ts,
                "source": "pytrends",
                "raw": {},
            }
        )
    return items


def fetch_trends(geo: str, limit: int = 10, use_pytrends_fallback: bool = False) -> List[Dict[str, Any]]:
    """Fetch trends from RSS; optionally fallback to pytrends."""
    try:
        return fetch_from_rss(geo=geo, limit=limit)
    except Exception as rss_err:
        logger.exception("RSS fetch failed", extra={"geo": geo, "error": str(rss_err)})
        if not use_pytrends_fallback:
            raise

    # Fallback
    try:
        return fetch_from_pytrends(geo=geo, limit=limit)
    except Exception as pt_err:
        logger.exception("pytrends fallback failed", extra={"geo": geo, "error": str(pt_err)})
        raise
