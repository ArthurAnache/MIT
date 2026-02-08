import os
import re
import html
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
        artist_obj = t.get("artist", {})
        artist = artist_obj.get("name") if isinstance(artist_obj, dict) else (artist_obj or "Unknown Artist")
        out.append({"track": name, "artist": artist})
    return out


def get_track_info(track: str, artist: str) -> dict:
    # contains wiki summary sometimes
    return _call_lastfm({"method": "track.getinfo", "track": track, "artist": artist})


def get_track_tags(track: str, artist: str, limit: int = 5) -> list[str]:
    try:
        data = _call_lastfm({"method": "track.gettoptags", "track": track, "artist": artist})
        tags = data.get("toptags", {}).get("tag", [])
        if isinstance(tags, dict):
            tags = [tags]
        names = [x.get("name") for x in tags if x.get("name")]
        return names[:limit]
    except Exception:
        return []


def get_artist_tags(artist: str, limit: int = 5) -> list[str]:
    try:
        data = _call_lastfm({"method": "artist.gettoptags", "artist": artist})
        tags = data.get("toptags", {}).get("tag", [])
        if isinstance(tags, dict):
            tags = [tags]
        names = [x.get("name") for x in tags if x.get("name")]
        return names[:limit]
    except Exception:
        return []


def _clean_summary(text: str, max_chars: int = 220) -> str:
    # Last.fm wiki summaries contain HTML + "Read more" links
    t = html.unescape(text or "")
    t = re.sub(r"<[^>]+>", "", t)  # strip HTML tags
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > max_chars:
        t = t[:max_chars].rstrip() + "…"
    return t
MOOD_TAGS = {
    "chill": "chill",
    "melancholic": "melancholic",
    "sad": "sad",
    "dark": "dark",
    "uplifting": "uplifting",
    "happy": "happy",
    "energetic": "energetic",
    "aggressive": "aggressive",
    "romantic": "romantic",
    "atmospheric": "atmospheric",
    "dreamy": "dreamy",
}
ENERGY_HINTS = {
    "dance": "high",
    "club": "high",
    "edm": "high",
    "dnb": "high",
    "drum and bass": "high",
    "jersey club": "high",
    "trap": "high",
    "ambient": "low",
    "lo-fi": "low",
    "acoustic": "low",
    "ballad": "low",
}
INSTRUMENT_HINTS = {
    "synthpop": "synths, bright plucks, wide pads",
    "electropop": "synths, electronic drums",
    "rnb": "smooth chords, tight drums, sub bass",
    "hip hop": "808s, punchy drums",
    "reggaeton": "dembow rhythm, latin percussion, sub bass",
    "rock": "electric guitars, live drums",
    "indie": "guitars, organic drums, warm bass",
    "soul": "warm keys, bass, live-feel drums",
}


def build_musicgen_description(track: str, artist: str, tags: list[str]) -> str:
    tags_l = [t.lower() for t in tags]

    # pick mood from tags if possible
    mood = None
    for k, v in MOOD_TAGS.items():
        if k in tags_l:
            mood = v
            break
    mood = mood or "focused"

    # rough energy hint
    energy = "medium"
    for k, v in ENERGY_HINTS.items():
        if k in tags_l:
            energy = v
            break

    # instrumentation hints (take up to 2)
    instr = []
    for k, v in INSTRUMENT_HINTS.items():
        if k in tags_l:
            instr.append(v)
        if len(instr) >= 2:
            break
    instr_text = "; ".join(instr) if instr else "modern production, clean mix"

    style = ", ".join(tags[:5]) if tags else "contemporary"

    return (
        f"Generate an original instrumental track inspired by the vibe of '{track}' by {artist}. "
        f"Genres: {style}. Mood: {mood}. Energy: {energy}. "
        f"Sound palette: {instr_text}. "
        f"Clear structure with a strong hook. No vocals."
    )


if __name__ == "__main__":
    top = get_top_tracks(limit=10)  # global (or country="United States")

    print("\nTop tracks with MusicGen-ready descriptions:\n")
    for i, item in enumerate(top, start=1):
        track = item["track"]
        artist = item["artist"]

        info = {}
        summary = None
        try:
            info = get_track_info(track, artist)
            summary = info.get("track", {}).get("wiki", {}).get("summary")
        except Exception:
            summary = None

        tags = get_track_tags(track, artist, limit=5)
        if not tags:
            tags = get_artist_tags(artist, limit=5)

        desc = build_musicgen_description(track, artist, tags)

        print(f"{i}. {track} — {artist}")
        print(f"   {desc}\n")
