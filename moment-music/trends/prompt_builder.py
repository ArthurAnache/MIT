"""Prompt builders for turning trends into MusicGen-ready text prompts.

We provide:
1) Deterministic template builder (stable, no external services)
2) Optional LLM hook (DeepSeek etc.) - stubbed interface

Prompt philosophy for MVP:
- English prompt is OK
- Include genre + vibe + key instruments + theme keywords
- Keep it short and directly usable by MusicGen
"""

from __future__ import annotations

import abc
from typing import List, Optional

from .models import PromptBundle, TrendTopic, UserProfile


class LLMPromptGenerator(abc.ABC):
    """Interface for an optional LLM-based prompt generator."""

    @abc.abstractmethod
    def generate_prompt(self, topic: TrendTopic, user: UserProfile) -> str:
        raise NotImplementedError


class StubLLMPromptGenerator(LLMPromptGenerator):
    """Stub that can be replaced by a real DeepSeek/HF implementation."""

    def generate_prompt(self, topic: TrendTopic, user: UserProfile) -> str:
        raise RuntimeError(
            "LLM prompt generation is not configured. "
            "Use the deterministic template or implement LLMPromptGenerator."
        )


def build_template_prompt(topic_title: str, user: UserProfile) -> str:
    """Deterministic prompt template suitable for MusicGen."""
    genre = user.default_genre or "electronic pop"
    vibe = user.default_vibe or "uplifting, modern"
    instruments = ", ".join(user.preferred_instruments or [])

    # Keep it direct. Mention the topic as a theme.
    prompt = (
        f"{genre}, {vibe}. "
        f"Main instruments: {instruments}. "
        f"Theme inspired by: {topic_title}. "
        "Catchy hook, clear rhythm, radio-ready structure, 120-140 BPM."
    )
    return prompt.strip()


def build_prompts(
    topics: List[TrendTopic],
    user: UserProfile,
    use_llm: bool = False,
    llm: Optional[LLMPromptGenerator] = None,
) -> List[PromptBundle]:
    """Build prompts for selected topics."""
    bundles: List[PromptBundle] = []
    llm = llm or StubLLMPromptGenerator()

    for t in topics:
        template_prompt = build_template_prompt(t.title, user)
        llm_prompt: Optional[str] = None
        if use_llm:
            try:
                llm_prompt = llm.generate_prompt(t, user)
            except Exception:
                # Keep it resilient: we still return template prompt.
                llm_prompt = None

        bundles.append(
            PromptBundle(
                topic_id=t.topic_id,
                topic_title=t.title,
                prompt_template=template_prompt,
                prompt_llm=llm_prompt,
            )
        )

    return bundles


def build_knowledge_vector(topics: List[TrendTopic], prompts: List[PromptBundle]) -> str:
    """Produce a compact knowledge vector text for Block 2.

    For MVP: concatenate theme lines; in future this could be structured JSON.
    """
    lines = []
    for t, p in zip(topics, prompts):
        lines.append(f"Trend: {t.title} | Prompt: {p.prompt_template}")
    return "\n".join(lines)
