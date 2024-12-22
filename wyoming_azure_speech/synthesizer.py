"""Synthesizer wrapper for Azure AI Speech Synthesizer."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import azure.cognitiveservices.speech as speechsdk

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

_LOGGER = logging.getLogger(__name__)


class AioPushAudioOutputStreamCallback(speechsdk.audio.PushAudioOutputStreamCallback):
    """An interface that defines callback methods for an audio output stream."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        """Initialize the audio output stream callback."""
        super().__init__()
        self._loop = loop
        self._audio_data: asyncio.Queue[bytes | None] = asyncio.Queue()

    def write(self, audio_buffer: memoryview) -> int:
        """Add synthesized audio samples."""
        _LOGGER.debug("Got synthesizer sample (%d bytes)", audio_buffer.nbytes)
        asyncio.run_coroutine_threadsafe(
            self._audio_data.put(audio_buffer.tobytes()),
            loop=self._loop,
        )
        return audio_buffer.nbytes

    def close(self) -> None:
        """Notifies that the stream is closed."""
        _LOGGER.debug("Synthesizer closed")
        asyncio.run_coroutine_threadsafe(self._audio_data.put(None), loop=self._loop)

    async def read(self) -> bytes:
        """Get synthesized audio samples from queue."""
        chunk = await self._audio_data.get()
        if chunk is None:
            raise StopAsyncIteration
        return chunk

    def __aiter__(self) -> AsyncIterator[bytes]:
        """Async interator for audio samples."""
        return self

    async def __anext__(self) -> bytes:
        """Async next operator for audio samples."""
        return await self.read()


class Synthesizer:
    """Azure Speech Services synthesizer."""

    def __init__(
        self,
        key: str,
        region: str,
        voice: str,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        """Initialize the Azure Speech Services synthesizer."""
        self._voice = voice
        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.speech_synthesis_voice_name = voice
        self._stream_callback = AioPushAudioOutputStreamCallback(loop)
        push_stream = speechsdk.audio.PushAudioOutputStream(self._stream_callback)
        audio_config = speechsdk.audio.AudioOutputConfig(stream=push_stream)
        self._speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        self._speech_synthesizer.synthesis_canceled.connect(self._canceled)
        self._speech_synthesizer.synthesis_completed.connect(self._completed)
        self._speech_synthesizer.synthesis_started.connect(self._started)

    def synthesize(self, text: str) -> None:
        """Start synthesizing the provided text."""
        self._synthesizer = self._speech_synthesizer.speak_text_async(text)

    def get_samples(self) -> AsyncIterator[bytes]:
        """Get iterator for synthesized audio samples."""
        return self._stream_callback

    @property
    def voice(self) -> str | None:
        """Get the voice used for synthesizing."""
        return self._voice

    def _started(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        _LOGGER.debug("Started: %s", evt)

    def _completed(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        _LOGGER.debug("Completed: %s", evt)
        self._stream_callback.close()

    def _canceled(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        details = evt.result.cancellation_details
        _LOGGER.error("Canceled: %s: %s %s", evt, details.reason, details.error_details)
        self._stream_callback.close()
