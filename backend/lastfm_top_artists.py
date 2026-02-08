import os
import requests

# 1) Read API key from environment variable
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_BASE_URL = "https://ws.audioscrobbler.com/2.0/"

def get_top_artists(limit=10, country=None):
    if not LASTFM_API_KEY:
        raise RuntimeError(
            "Variable d'environnement LASTFM_API_KEY non définie.\n"
            "Fais: export LASTFM_API_KEY=\"ta_clef\""
        )

    # 2) Choose endpoint
    if country:
        params = {
            "method": "geo.gettopartists",
            "country": country,
            "limit": limit,
        }
    else:
        params = {
            "method": "chart.gettopartists",
            "limit": limit,
        }

    # 3) Common parameters
    params["api_key"] = LASTFM_API_KEY
    params["format"] = "json"

    # 4) HTTP request
    response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    # 5) Last.fm sometimes returns errors with HTTP 200
    if "error" in data:
        raise RuntimeError(f"Last.fm error {data['error']}: {data.get('message')}")

    # 6) Extract artists
    if country:
        artists = data["topartists"]["artist"]
    else:
        artists = data["artists"]["artist"]

    # 7) Format output
    results = []
    for artist in artists[:limit]:
        results.append({
            "rank": int(artist.get("@attr", {}).get("rank", 0)),
            "name": artist["name"],
            "listeners": int(artist.get("listeners", 0)),
        })

    return results

def get_artist_tags(artist_name, limit=3):
    params = {
        "method": "artist.gettoptags",
        "artist": artist_name,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }

    r = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    if "error" in data:
        return []

    tags = data.get("toptags", {}).get("tag", [])

    # parfois un seul tag -> dict
    if isinstance(tags, dict):
        tags = [tags]

    # on garde juste les noms
    return [t["name"] for t in tags[:limit]]

# 8) Script entry point
if __name__ == "__main__":
    # Choose ONE of the two lines below
    #top10 = get_top_artists(limit=10, country="United States")  
    
    top10 = get_top_artists(limit=10)  # Top global

    print("\nTop 10 trending artists:\n")

    for i, a in enumerate(top10, start=1):
        tags = get_artist_tags(a["name"], limit=3)
        style = ", ".join(tags) if tags else "unknown style"
        print(f"{i}. {a['name']} — {style}")


# backend/lastfm_top_artists.py

def main_lastfm_top_artists(geo=None, limit=20):
    """
    Appelable depuis l'API.
    Renvoie la liste des artistes trending.
    """
    # TON CODE EXISTANT ICI
    # (appel API Last.fm, récupération artistes, tags, etc.)

    return [
        {
            "name": "Kendrick Lamar",
            "tags": ["hip hop", "rap"],
        },
        # ...
    ]


# OPTIONNEL : uniquement pour tester à la main
if __name__ == "__main__":
    res = main_lastfm_top_artists()
    print(res[:3])

