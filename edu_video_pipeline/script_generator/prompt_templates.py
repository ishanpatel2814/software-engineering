"""
Prompt templates for generating educational scripts with OpenAI.
Backwards-compatible: exports `get_prompt_for_content_type(...)`.
"""

from __future__ import annotations
from typing import List, Dict, Any

# Phrases that make narration sound canned
BANNED_PHRASES: List[str] = [
    "let's dive in", "let’s dive in", "let us dive in",
    "let's get started", "let’s get started",
    "welcome to", "in this slide", "on this slide",
    "in this lecture", "in today's lecture", "in todays lecture",
    "now let's", "now let’s", "moving on",
    "next we will", "next we'll", "as we can see here",
    "here we have", "without further ado",
    "let's take a look", "let’s take a look",
]

STYLE_RULES = """
Tone & style:
- Plain-spoken, warm, direct. No hype, no ceremony.
- Do NOT use any of these phrases: {banned}
- Explain as if to a smart friend seeing this for the first time.
- Prefer concrete examples and small numbers.
- Use first-person sparingly; avoid repetitive “let’s …”.

Structure:
- Anchor the core idea in 1–2 sentences.
- Then explain step-by-step, each step tied to a tiny, relatable example.
- End with a one-line recap (“So now you know …”).
"""

# ---------- Whole-script prompt ----------
EDUCATIONAL_PROMPT = """
Transform the content below into a natural teaching script.

{style_rules}

Content to cover:
-----------------
{content}

Constraints:
- No references to slides/sections/presentation flow.
- No meta talk like “today we will…”, “in this lecture…”.
- Keep transitions invisible; connect ideas by logic, not by signaling.
- Aim for ~{approx_words} words (flex if needed for clarity).
"""

# ---------- Per-segment (recommended) ----------
SEGMENT_SCRIPT_PROMPT = """
Write a natural narration for this segment.

{style_rules}

Topic: {topic}
Objectives (optional): {objectives}
Key points (from the slide):
{bullets}

Speaker notes (if any):
{notes}

Context to maintain continuity:
Previous segment summary (optional): {prev_summary}

Constraints:
- Focus only on this segment’s points; do not foreshadow future slides.
- No cliché openings or slide language (see banned list).
- Target ~{approx_words} words so it reads aloud in ~{target_seconds} seconds.
"""

# ---------- Concept-only ----------
CONCEPT_EXPLANATION_PROMPT = """
Explain the concept below in a clear, conversational way.

{style_rules}

Concept: {concept}
Context: {context}

Constraints:
- Start with a simple, intuitive definition.
- Give one concrete, relatable example or analogy.
- Explain why it matters / how it’s used.
- Avoid academic/formal phrasing and rhetorical fluff.
- No meta talk (“let me explain…”).
"""

# ---------- Transition ----------
SECTION_TRANSITION_PROMPT = """
Write a natural bridge between two topics without obvious “now we move on” phrasing.

First topic: {topic1}
Second topic: {topic2}

Constraints:
- Highlight the logical connection in 1–3 sentences.
- No “moving on”, “next we’ll…”, or similar.
- Keep the same friendly teaching tone.
"""

# ---------- Helpers ----------
def words_for_duration(seconds: float, wpm: int = 145) -> int:
    """Approx words that fit into `seconds` at `wpm` speaking rate."""
    if seconds <= 0:
        return 160
    return max(80, int(seconds * (wpm / 60)))

def get_prompt_for_script(content: str, approx_words: int = 180) -> str:
    return EDUCATIONAL_PROMPT.format(
        style_rules=STYLE_RULES.format(banned=", ".join(BANNED_PHRASES)),
        content=content,
        approx_words=approx_words,
    )

def get_prompt_for_segment(
    topic: str,
    bullets: str,
    notes: str = "",
    objectives: str = "",
    prev_summary: str = "",
    target_seconds: float = 12.0,
    wpm: int = 145,
) -> str:
    approx_words = words_for_duration(target_seconds, wpm=wpm)
    return SEGMENT_SCRIPT_PROMPT.format(
        style_rules=STYLE_RULES.format(banned=", ".join(BANNED_PHRASES)),
        topic=(topic or "").strip() or "(untitled)",
        objectives=(objectives or "").strip() or "—",
        bullets=(bullets or "").strip() or "—",
        notes=(notes or "").strip() or "—",
        prev_summary=(prev_summary or "").strip() or "—",
        approx_words=approx_words,
        target_seconds=int(target_seconds),
    )

def get_prompt_for_concept(concept: str, context: str = "") -> str:
    return CONCEPT_EXPLANATION_PROMPT.format(
        style_rules=STYLE_RULES.format(banned=", ".join(BANNED_PHRASES)),
        concept=concept,
        context=context,
    )

def get_prompt_for_transition(topic1: str, topic2: str) -> str:
    return SECTION_TRANSITION_PROMPT.format(topic1=topic1, topic2=topic2)

# ---------- Back-compat shim ----------
def get_prompt_for_content_type(content_type: str, **kwargs) -> str:
    """
    Legacy entrypoint used by script_processor.
    Valid: 'script' | 'segment' | 'slide' | 'concept' | 'transition'
    """
    ct = (content_type or "").lower()
    if ct == "script":
        return get_prompt_for_script(
            kwargs.get("content", ""),
            kwargs.get("approx_words", 180),
        )
    if ct in ("segment", "slide"):
        return get_prompt_for_segment(
            topic=kwargs.get("topic", ""),
            bullets=kwargs.get("bullets", ""),
            notes=kwargs.get("notes", ""),
            objectives=kwargs.get("objectives", ""),
            prev_summary=kwargs.get("prev_summary", ""),
            target_seconds=float(kwargs.get("target_seconds", 12.0)),
            wpm=int(kwargs.get("wpm", 145)),
        )
    if ct == "concept":
        return get_prompt_for_concept(
            kwargs.get("concept", ""),
            kwargs.get("context", ""),
        )
    if ct == "transition":
        return get_prompt_for_transition(
            kwargs.get("topic1", ""),
            kwargs.get("topic2", ""),
        )
    raise ValueError(f"Unknown content type: {content_type}")
