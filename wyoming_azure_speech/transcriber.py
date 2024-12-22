"""Transcription wrapper for Azure AI Speech Recognizer."""

from __future__ import annotations

import logging
from asyncio import Event

import azure.cognitiveservices.speech as speechsdk

_LOGGER = logging.getLogger(__name__)


class Transcriber:
    """Azure Speech Services Transcriber."""

    def __init__(self, key: str, region: str, language: str) -> None:
        """Initialize the Azure Speech Services Transcriber."""
        self._language = language
        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        self._stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=self._stream)
        self._speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
            language=language,
        )

        self._speech_recognizer.recognizing.connect(self._recognizing)
        self._speech_recognizer.recognized.connect(self._recognized)
        self._speech_recognizer.session_started.connect(self._session_started)
        self._speech_recognizer.session_stopped.connect(self._setssion_stopped)
        self._speech_recognizer.canceled.connect(self._canceled)

        self._recognition_finished = Event()
        self._recognized_statements: list[str] = []

    def start(self) -> None:
        """Start transcription process."""
        self._speech_recognizer.start_continuous_recognition()

    def stop(self) -> None:
        """Stop transcription process."""
        self._speech_recognizer.stop_continuous_recognition()

    def push_sample(self, sample: bytes) -> None:
        """Provide audio sample for transcribing."""
        self._stream.write(sample)

    @property
    def language(self) -> str | None:
        """Get the languages used for transcribing."""
        return self._language

    @property
    async def recognized_statement(self) -> str:
        """Wait and get the recognized statement."""
        await self._recognition_finished.wait()
        return " ".join(self._recognized_statements)

    def _session_started(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        _LOGGER.debug("Session started: %s", evt)

    def _setssion_stopped(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        _LOGGER.debug("Session stopped: %s", evt)

    def _recognizing(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        _LOGGER.debug("Recognizing: %s", evt)

    def _recognized(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        _LOGGER.debug("Recognized: %s", evt)
        self._recognized_statements.append(evt.result.text)
        self._recognition_finished.set()

    def _canceled(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        _LOGGER.debug("Canceled: %s", evt)
        self._recognition_finished.set()
