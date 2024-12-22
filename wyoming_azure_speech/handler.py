"""Event handler for clients of the server."""

import asyncio
import logging
from typing import TYPE_CHECKING

from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.info import Describe, Info
from wyoming.server import AsyncEventHandler
from wyoming.tts import Synthesize

from .speech_service import SpeechService

if TYPE_CHECKING:
    from .transcriber import Transcriber

_LOGGER = logging.getLogger(__name__)


class AzureSpeechEventHandler(AsyncEventHandler):
    """Event handler for clients."""

    def __init__(
        self,
        wyoming_info: Info,
        speech_service: SpeechService,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Initialize Wyoming server event handler."""
        super().__init__(reader=reader, writer=writer)

        self._wyoming_info_event = wyoming_info.event()
        self._speech_service = speech_service
        self._transcriber: Transcriber | None = None

    async def handle_event(self, event: Event) -> bool:
        """Handle an event. Returning false will disconnect the client."""
        event_to_handler = {
            AudioChunk: self._audio_chunk,
            AudioStart: self._audio_start,
            AudioStop: self._audio_stop,
            Transcribe: self._transcribe,
            Synthesize: self._synthesize,
            Describe: self._describe,
        }

        for event_type, handler in event_to_handler.items():
            if event_type.is_type(event.type):
                return await handler(event)

        return True

    async def _audio_chunk(self, event: Event) -> bool:
        if self._transcriber is None:
            msg = "Got 'AudioChunk' without 'Transcribe' event"
            raise RuntimeError(msg)
        chunk = AudioChunk.from_event(event)
        self._transcriber.push_sample(chunk.audio)
        return True

    async def _audio_start(self, _: Event) -> bool:
        _LOGGER.debug("Audio start")
        if self._transcriber is None:
            msg = "Got 'AudioStart' without 'Transcribe' event"
            raise RuntimeError(msg)
        self._transcriber.start()
        return True

    async def _audio_stop(self, _: Event) -> bool:
        _LOGGER.debug("Audio stop")
        if self._transcriber is None:
            msg = "Got 'AudioStop' without 'Transcribe' event"
            raise RuntimeError(msg)
        self._transcriber.stop()
        text = await self._transcriber.recognized_statement
        _LOGGER.info("Transcription result: '%s'", text)
        await self.write_event(Transcript(text=text).event())
        self._transcriber = None
        return False

    async def _transcribe(self, event: Event) -> bool:
        _LOGGER.debug("Transcribe")
        transcribe = Transcribe.from_event(event)
        self._transcriber = self._speech_service.create_transcriber(
            transcribe.language,
        )
        _LOGGER.info("Starting transcription for '%s'", self._transcriber.language)
        return True

    async def _synthesize(self, event: Event) -> bool:
        _LOGGER.debug("Synthesize")
        synthesize = Synthesize.from_event(event)
        synthesizer = self._speech_service.create_synthesizer(
            synthesize.voice.name if synthesize.voice is not None else None,
        )
        _LOGGER.info(
            "Starting synthesizing '%s' with '%s'",
            synthesize.text,
            synthesizer.voice,
        )
        synthesizer.synthesize(synthesize.text)

        await self.write_event(AudioStart(rate=16000, width=2, channels=1).event())
        async for sample in synthesizer.get_samples():
            await self.write_event(
                AudioChunk(audio=sample, rate=16000, width=2, channels=1).event(),
            )
        await self.write_event(AudioStop().event())
        _LOGGER.info("Finished sending synthesized audio")
        return True

    async def _describe(self, _: Event) -> bool:
        _LOGGER.debug("Describe")
        await self.write_event(self._wyoming_info_event)
        return True
