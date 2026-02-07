from datetime import datetime, timezone

from trends.models import UserProfile
from trends.prompt_builder import build_template_prompt
from trends.scoring import score_and_filter


def test_prompt_contains_genre_vibe_instruments():
    user = UserProfile(
        user_id="u1",
        interests=["tech"],
        avoid=[],
        default_genre="ambient",
        default_vibe="calm, dreamy",
        preferred_instruments=["piano", "pads"],
        language="fr",
    )
    p = build_template_prompt("Mars mission", user)
    assert "ambient" in p
    assert "calm" in p
    assert "piano" in p
    assert "Mars mission" in p


def test_scoring_downranks_avoid_keywords():
    user = UserProfile(
        user_id="u2",
        interests=[],
        avoid=["politics"],
        default_genre="electronic",
        default_vibe="energetic",
        preferred_instruments=["synth"],
        language="fr",
    )

    raw = [
        {
            "topic_id": "1",
            "title": "Election results in France",
            "timestamp": datetime.now(timezone.utc),
            "source": "test",
            "raw": {},
        },
        {
            "topic_id": "2",
            "title": "New AI model release",
            "timestamp": datetime.now(timezone.utc),
            "source": "test",
            "raw": {},
        },
    ]

    scored = score_and_filter(raw, user, remove_hard_blocks=False)
    # AI should rank above election due to avoid downrank
    assert scored[0].topic_id == "2"
    assert scored[1].topic_id == "1"
