"""Service wrapper for Azure AI Speech Service."""

from __future__ import annotations

import asyncio
from functools import cached_property
from itertools import groupby
from operator import itemgetter
from typing import Any

import requests

from .synthesizer import Synthesizer
from .transcriber import Transcriber


class SpeechService:
    """Factory class to create speech services."""

    def __init__(
        self,
        key: str,
        region: str,
        transcription_language: str = "en-US",
        default_voice: str = "en-US-AvaMultilingualNeural",
    ) -> None:
        """Initialize the speech service."""
        self._key = key
        self._region = region
        self._default_transcription_language = transcription_language
        self._default_voice = default_voice

    @cached_property
    def transcription_languages(self) -> list[str]:
        """Get list of supported transription languages."""
        with requests.get(
            f"https://{self._region}.api.cognitive.microsoft.com//speechtotext/v3.2/transcriptions/locales",
            headers={"Ocp-Apim-Subscription-Key": self._key},
            timeout=60,
        ) as response:
            json = response.json()
            if not response.ok:
                raise RuntimeError(json.get("error", {}).get("message", ""))
            return json

    @cached_property
    def synthesization_voices(self) -> dict[str, list[dict[str, Any]]]:
        """Get list of supported synthesization voices."""
        with requests.get(
            f"https://{self._region}.tts.speech.microsoft.com/cognitiveservices/voices/list",
            headers={"Ocp-Apim-Subscription-Key": self._key},
            timeout=60,
        ) as response:
            json = response.json()
            if not response.ok:
                msg = "Failed getting list of voices"
                raise RuntimeError(msg)
        json = sorted(json, key=itemgetter("Locale"))
        self._supported_voices = [voice["ShortName"] for voice in json]
        return {
            language: list(voices)
            for language, voices in groupby(json, key=itemgetter("Locale"))
        }

    def create_transcriber(self, language: str | None = None) -> Transcriber:
        """Create transcriber object."""
        language = (
            language if language is not None else self._default_transcription_language
        )
        if language not in self.transcription_languages:
            msg = f"Unsupported language: '{language}'"
            raise ValueError(msg)
        return Transcriber(
            self._key,
            self._region,
            language,
        )

    def create_synthesizer(self, voice: str | None = None) -> Synthesizer:
        """Create synthesizer object."""
        voice = voice if voice is not None else self._default_voice
        if voice not in self._supported_voices:
            msg = f"Unsupported voice: '{voice}'"
            raise ValueError(msg)
        return Synthesizer(
            self._key,
            self._region,
            voice,
            asyncio.get_event_loop(),
        )
