# script_generator/sanitizer.py
from __future__ import annotations
import re

# Phrases we never want in the narration
BANNED_PATTERNS = [
    r"\blet'?s dive in\b",
    r"\blet’?s dive in\b",
    r"\blet'?s get started\b",
    r"\blet’?s get started\b",
    r"\bwelcome to\b",
    r"\bin (this|the) (slide|lecture|section)\b",
    r"\bnow let'?s\b",
    r"\bnow let’?s\b",
    r"\bmoving on\b",
    r"\bnext (we('?| wi)ll|up)\b",
    r"\bas we can see here\b",
    r"\bhere we have\b",
    r"\bwithout further ado\b",
    r"\blet'?s take a look\b",
    r"\blet’?s take a look\b",
]

_WHITESPACE_FIXES = [
    (r"[ \t]{2,}", " "),
    (r"\n{3,}", "\n\n"),
    (r" +([,.;:!?])", r"\1"),   # remove space before punctuation
    (r"\( +", "("),             # tidy spaces after opening paren
    (r" +\)", ")"),             # tidy spaces before closing paren
]

def sanitize_script(text: str) -> str:
    """Remove stock phrases and tidy whitespace without changing meaning."""
    cleaned = text or ""
    for pat in BANNED_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

    # collapse any leftover “stubs” from removals
    for pat, repl in _WHITESPACE_FIXES:
        cleaned = re.sub(pat, repl, cleaned)

    # trim dangling punctuation and whitespace at line starts
    cleaned = re.sub(r"^\s*[,.;:!?]\s*", "", cleaned, flags=re.MULTILINE)

    return cleaned.strip()
