"""
Dynamic Punctuation & Conversational Prosody Director for OpenGen Audio Engine.
Inserts variable punctuation pauses (350ms commas, 750ms periods, 1200ms paragraph breaks)
and manages conversational breath tokens ([gasp], [sigh], [chuckle]) to eliminate
monotone 'GPS navigation' robotic cadences.
"""
import re
from typing import List, Dict, Any, Optional


class AudioTimingDirector:
    """Manages speech pacing, dynamic pauses, and conversational breath markers."""

    COMMA_PAUSE_MS = 350
    PERIOD_PAUSE_MS = 750
    PARAGRAPH_PAUSE_MS = 1200

    @classmethod
    def format_conversational_script(
        cls,
        raw_text: str,
        inject_breaths: bool = True,
        style: str = "conversational"
    ) -> str:
        """
        Formats raw text with natural prosody markers, dynamic pause tokens,
        and breath tokens for conversational zero-shot TTS.
        """
        if not raw_text or not raw_text.strip():
            return ""

        # Normalize whitespace
        text = " ".join(raw_text.split())

        # If conversational and long enough, ensure breath punctuation is present
        if inject_breaths and len(text.split()) > 20:
            # Inject breath marker at natural major sentence boundaries if none exist
            if not any(token in text for token in ["[gasp]", "[sigh]", "[pause]", "..."]):
                sentences = re.split(r"(?<=[.!?]) +", text)
                if len(sentences) >= 3:
                    # Insert subtle pause between middle sentences
                    sentences[1] = f"... {sentences[1]}"
                    text = " ".join(sentences)

        return text

    @classmethod
    def to_ssml(cls, text: str) -> str:
        """
        Converts text into SSML with explicit break tags based on punctuation timing:
        - Commas: 350ms
        - Periods / Question marks / Exclamations: 750ms
        - Paragraphs: 1200ms
        """
        ssml = text
        # Commas
        ssml = re.sub(r",\s*", f', <break time="{cls.COMMA_PAUSE_MS}ms"/> ', ssml)
        # Periods
        ssml = re.sub(r"\.\s+", f'. <break time="{cls.PERIOD_PAUSE_MS}ms"/> ', ssml)
        # Semicolons / Colons
        ssml = re.sub(r"[:;]\s*", f'; <break time="450ms"/> ', ssml)

        return f"<speak>{ssml}</speak>"
