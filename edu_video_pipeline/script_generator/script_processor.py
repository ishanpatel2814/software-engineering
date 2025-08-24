"""
Script generator for creating educational scripts from content.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Any

from script_generator.openai_client import OpenAIClient
from script_generator.prompt_templates import get_prompt_for_content_type
from utils.timing import calculate_speaking_rate

# Optional sanitizer (if file exists). If not, this becomes a no-op.
try:
    from script_generator.sanitizer import sanitize_script  # type: ignore
except Exception:  # pragma: no cover
    def sanitize_script(text: str) -> str:
        return text

logger = logging.getLogger("edu_video_pipeline")


class ScriptGenerator:
    """Generator for creating educational scripts from content."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the script generator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.openai_client = OpenAIClient(config)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def generate_script(self, content_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an educational script from content structure.

        Args:
            content_structure: Structured content data. Expected shape:
                {
                  "title": "...",
                  "sections": [
                    {
                      "title": "...",            # optional
                      "text": "...",             # optional narrative text
                      "key_points": [...],       # optional list
                      "notes": "...",            # optional speaker notes
                      "objectives": "...",       # optional
                      "target_seconds": 12.0,    # optional per-section duration hint
                      ...
                    }, ...
                  ]
                }

        Returns:
            Dictionary containing the generated script
        """
        logger.info("Generating educational script")

        sections = content_structure.get("sections", []) or []
        script_sections: List[Dict[str, Any]] = []

        prev_summary = ""  # brief continuity hint for the next segment

        for idx, section in enumerate(sections, start=1):
            logger.debug(f"Generating script for section {idx}/{len(sections)}")
            section_script = self._generate_section_script(section, prev_summary)
            script_sections.append(section_script)
            prev_summary = self._brief_summary(section_script["text"])

        # Generate transitions between sections
        if len(script_sections) > 1:
            for i in range(len(script_sections) - 1):
                transition = self._generate_transition(
                    script_sections[i]["title"], script_sections[i + 1]["title"]
                )
                script_sections[i]["transition"] = transition

        # Assemble final script
        total_duration = sum(s["timing"]["duration"] for s in script_sections)
        total_words = sum(s["timing"]["word_count"] for s in script_sections)

        script = {
            "title": content_structure.get("title", "Educational Script"),
            "sections": script_sections,
            "metadata": {
                "total_duration": total_duration,
                "word_count": total_words,
                "section_count": len(script_sections),
            },
        }

        logger.info(
            f"Generated script with {len(script_sections)} sections, "
            f"{total_words} words, {total_duration:.2f} seconds"
        )
        return script

    def add_timing_markers(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add start/end timing markers to each section.
        """
        marked = {**script}
        marked["sections"] = []
        current_time = 0.0

        for section in script.get("sections", []):
            s = {**section}
            s["start_time"] = current_time
            s["end_time"] = current_time + section["timing"]["duration"]
            marked["sections"].append(s)
            current_time = s["end_time"]

        marked["metadata"] = {**script.get("metadata", {})}
        marked["metadata"]["total_duration"] = current_time
        return marked

    def validate_script(self, script: Dict[str, Any]) -> bool:
        """
        Validate the script structure.
        """
        if "sections" not in script or not script["sections"]:
            logger.error("Script has no sections")
            return False

        for i, sec in enumerate(script["sections"], start=1):
            if not sec.get("text"):
                logger.error(f"Section {i} has no text")
                return False
            if "timing" not in sec:
                logger.error(f"Section {i} has no timing information")
                return False

        return True

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _generate_section_script(self, section: Dict[str, Any], prev_summary: str) -> Dict[str, Any]:
        """
        Generate narration for a single section (segment-level prompt preferred).
        """
        try:
            # Prepare segment inputs
            title = self._extract_title(section.get("title") or section.get("text", ""))
            bullets = self._format_bullets(section.get("key_points", []))
            notes = (section.get("notes") or "").strip()
            objectives = (section.get("objectives") or "").strip()
            target_seconds = self._estimate_target_seconds(section)

            # Preferred: segment prompt (back-compat shim supports this type)
            try:
                prompt = get_prompt_for_content_type(
                    "segment",
                    topic=title,
                    bullets=bullets,
                    notes=notes,
                    objectives=objectives,
                    prev_summary=prev_summary,
                    target_seconds=target_seconds,
                    wpm=int(self.config.get("WORDS_PER_MINUTE", 150)),
                )
            except Exception:
                # Fallback to whole-script-style prompt if older templates are present
                legacy_blob = self._prepare_section_content(section)
                prompt = get_prompt_for_content_type("script", content=legacy_blob)

            # Call model
            response = self.openai_client.generate_completion(prompt)
            text = self.openai_client.handle_response(response)

            # Post-process (strip slide-y/meta phrases, sanitize clichés if available)
            text = self.post_process_script(sanitize_script(text))

            # Compute timing from final text
            timing = self._calculate_timing(text)

            return {
                "title": title or "Section",
                "text": text,
                "transition": "",
                "timing": timing,
            }

        except Exception as e:
            logger.error(f"Error generating section script: {e}")
            raise

    def _generate_transition(self, topic1: str, topic2: str) -> str:
        """
        Generate a short, natural bridge between two topics.
        """
        try:
            prompt = get_prompt_for_content_type("transition", topic1=topic1, topic2=topic2)
            response = self.openai_client.generate_completion(prompt)
            text = self.openai_client.handle_response(response)
            text = self.post_process_script(sanitize_script(text))
            return text
        except Exception as e:
            logger.error(f"Error generating transition: {e}")
            return ""

    def _prepare_section_content(self, section: Dict[str, Any]) -> str:
        """
        Legacy: build a flat content blob for 'script' prompts.
        """
        text = (section.get("text") or "").strip()
        key_points = section.get("key_points", []) or []

        if key_points:
            text += "\n\nKey Points:\n"
            for point in key_points:
                if point:
                    text += f"- {str(point).strip()}\n"

        notes = (section.get("notes") or "").strip()
        if notes:
            text += "\n\nSpeaker Notes:\n" + notes

        return text.strip()

    def _format_bullets(self, items: List[Any]) -> str:
        """
        Format key points (one per line) for the segment prompt.
        """
        out: List[str] = []
        for it in items or []:
            s = str(it).strip()
            if s:
                out.append(f"- {s}")
        return "\n".join(out)

    def post_process_script(self, script_text: str) -> str:
        """
        Remove slide-y/meta phrasing and normalize whitespace.
        """
        patterns = [
            r"(?i)welcome to (?:today's|this) (?:lecture|presentation|lesson|slide|topic)",
            r"(?i)in this (?:slide|presentation|lecture|section)",
            r"(?i)let'?s (?:move on to|proceed to|continue with|get started|dive in)(?: the)?(?: next)?(?: slide| topic| section)?",
            r"(?i)in the next (?:slide|section|part)",
            r"(?i)as (?:we can|you can) see (?:in|on) this (?:slide|image|figure)",
            r"(?i)on this (?:slide|page)",
            r"(?i)today,? (?:we will|we'll|I will|I'll) (?:be )?(?:discussing|talking about|exploring|learning about)",
            r"(?i)thank you for (?:your attention|listening)",
            r"(?i)without further ado",
            r"(?i)let'?s take a look",
        ]

        cleaned = script_text or ""
        for pat in patterns:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

        # whitespace tidy
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _extract_title(self, content: str) -> str:
        """
        Extract a concise title from a text-like string.
        """
        if not content:
            return "Section"
        lines = [ln.strip() for ln in str(content).splitlines() if ln.strip()]
        if not lines:
            return "Section"
        title = lines[0]
        return (title[:47] + "...") if len(title) > 50 else title

    def _estimate_target_seconds(self, section: Dict[str, Any]) -> float:
        """
        Estimate a target narration length (seconds) for a section.
        Priority:
          1) section['target_seconds'] if provided (>0)
          2) derive from text+bullets+notes and WORDS_PER_MINUTE
          3) default fallback
        """
        try:
            if "target_seconds" in section and float(section["target_seconds"]) > 0:
                return float(section["target_seconds"])
        except Exception:
            pass

        wpm = float(self.config.get("WORDS_PER_MINUTE", 150))
        blob = " ".join([
            section.get("text", "") or "",
            " ".join(map(str, section.get("key_points", []) or [])),
            section.get("notes", "") or "",
        ]).strip()

        wc = len(re.findall(r"\S+", blob))
        if wc > 0 and wpm > 0:
            dur = wc * 60.0 / wpm
            # clamp to a practical range for slide segments
            return max(6.0, min(40.0, dur))

        return float(self.config.get("DEFAULT_SECTION_SECONDS", 12.0))

    def _calculate_timing(self, script_text: str) -> Dict[str, Any]:
        """
        Calculate timing info based on the final narration text.
        """
        words = re.findall(r"\S+", script_text or "")
        word_count = len(words)

        words_per_minute = int(self.config.get("WORDS_PER_MINUTE", 150))
        duration = calculate_speaking_rate(script_text, words_per_minute)

        duration_multiplier = float(self.config.get("DURATION_MULTIPLIER", 1.0))
        adjusted_duration = duration * duration_multiplier

        return {
            "word_count": word_count,
            "duration": adjusted_duration,
            "speaking_rate": words_per_minute,
        }

    def _brief_summary(self, text: str, max_sents: int = 2) -> str:
        """
        Grab the first 1–2 sentences to help the next segment stay coherent.
        """
        sents = re.split(r"(?<=[.!?])\s+", (text or "").strip())
        return " ".join(sents[:max_sents]).strip() if sents else ""
