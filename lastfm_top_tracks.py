import os
import requests

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_BASE_URL = "https://ws.audioscrobbler.com/2.0/"


def _call_lastfm(params: dict) -> dict:
    if not LASTFM_API_KEY:
        raise RuntimeError(
            "Variable d'environnement LASTFM_API_KEY non définie.\n"
            "Fais: export LASTFM_API_KEY=\"ta_clef\""
        )

    params = dict(params)
    params["api_key"] = LASTFM_API_KEY
    params["format"] = "json"

    r = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    if "error" in data:
        raise RuntimeError(f"Last.fm error {data['error']}: {data.get('message')}")

    return data


def get_top_tracks(limit: int = 10, country: str | None = None) -> list[dict]:
    if country:
        data = _call_lastfm({"method": "geo.gettoptracks", "country": country, "limit": limit})
        tracks = data.get("toptracks", {}).get("track", [])
    else:
        data = _call_lastfm({"method": "chart.gettoptracks", "limit": limit})
        tracks = data.get("tracks", {}).get("track", [])

    if isinstance(tracks, dict):
        tracks = [tracks]

    out = []
    for t in tracks[:limit]:
        name = t.get("name", "Unknown Track")
        artist = (t.get("artist", {}) or {}).get("name") if isinstance(t.get("artist"), dict) else t.get("artist")
        if not artist:
            artist = "Unknown Artist"
        out.append({"track": name, "artist": artist})
    return out


def get_track_tags(track: str, artist: str, limit: int = 3) -> list[str]:
    # First try: tags on the track itself
    try:
        data = _call_lastfm({"method": "track.gettoptags", "track": track, "artist": artist})
        tags = data.get("toptags", {}).get("tag", [])
        if isinstance(tags, dict):
            tags = [tags]
        names = [x.get("name") for x in tags if x.get("name")]
        return names[:limit]
    except Exception:
        return []


def get_artist_tags(artist: str, limit: int = 3) -> list[str]:
    # Fallback: artist tags
    try:
        data = _call_lastfm({"method": "artist.gettoptags", "artist": artist})
        tags = data.get("toptags", {}).get("tag", [])
        if isinstance(tags, dict):
            tags = [tags]
        names = [x.get("name") for x in tags if x.get("name")]
        return names[:limit]
    except Exception:
        return []


if __name__ == "__main__":
    # Choose ONE:
    top = get_top_tracks(limit=10)  # global
    # top = get_top_tracks(limit=10, country="United States")  # by country

    print("\nTop 10 trending tracks:\n")
    for i, item in enumerate(top, start=1):
        track = item["track"]
        artist = item["artist"]

        tags = get_track_tags(track, artist, limit=3)
        if not tags:
            tags = get_artist_tags(artist, limit=3)

        style = ", ".join(tags) if tags else "unknown style"
        print(f"{i}. {track} — {artist} — {style}")
