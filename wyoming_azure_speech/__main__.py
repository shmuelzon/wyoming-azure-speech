#!/usr/bin/env python3
"""Wyoming Asure Speech Service Entrypoint."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import os
import sys
from functools import partial
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
from wyoming.info import AsrModel, AsrProgram, Attribution, Info, TtsProgram, TtsVoice
from wyoming.server import AsyncServer

from .handler import AzureSpeechEventHandler
from .speech_service import SpeechService

_LOGGER = logging.getLogger(__name__)


async def main() -> None:
    """Entrypoint function."""
    args = parse_arguments()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format=args.log_format,
    )

    _LOGGER.debug(args)
    parse_environment(args)
    validate_arguments(args)

    speech_service = SpeechService(
        args.key,
        args.region,
        args.transcription_language,
        args.voice,
    )
    transcription_languages = get_transcription_languages(speech_service)
    synthesization_voices = get_synthesization_voices(speech_service)
    server = AsyncServer.from_uri(args.uri)
    _LOGGER.info("Starting server")
    await server.run(
        partial(
            AzureSpeechEventHandler,
            await wyoming_information(transcription_languages, synthesization_voices),
            speech_service,
        ),
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--key", help="Microsoft Azure key")
    parser.add_argument(
        "--region",
        help="Microsoft Azure region name (westeurope, eastus, etc.)",
    )
    parser.add_argument(
        "--uri",
        default="tcp://0.0.0.0:10300",
        help="unix:// or tcp://",
    )
    parser.add_argument(
        "--transcription-language",
        default="en-US",
        help="Default language to set for transcription",
    )
    parser.add_argument(
        "--voice",
        default="en-US-AvaMultilingualNeural",
        help="Default voice to set for synthesizing",
    )
    parser.add_argument("--debug", action="store_true", help="Log DEBUG messages")
    parser.add_argument(
        "--log-format",
        default="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
        help="Format for log messages",
    )
    return parser.parse_args()


def parse_environment(args: argparse.Namespace) -> None:
    """Load argument defaults from environment variables."""
    if not args.key:
        args.key = load_optional_param_from_env("AZURE_KEY")
    if not args.region:
        args.region = load_optional_param_from_env("AZURE_REGION")


def load_optional_param_from_env(param_name: str) -> str | None:
    """Load parameter value from environment variable."""
    if param_name in os.environ:
        return os.environ[param_name]

    param_name_file = f"{param_name}_FILE"
    if param_name_file not in os.environ:
        return None

    file_name = os.environ[param_name_file]
    try:
        with Path(file_name).open() as file:
            return file.read().strip()
    except Exception:
        _LOGGER.exception("Failed loading value from {file_name}")
    return None


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if not args.key or not args.region:
        _LOGGER.error("Microsoft Azure region and key must be specified")
        sys.exit(-1)


async def wyoming_information(
    transcription_languages: list[str],
    synthesization_voices: list[TtsVoice],
) -> Info:
    """Generate Wyoming description for supported services."""
    return Info(
        asr=[
            AsrProgram(
                name="Azure AI Speech",
                description="Microsoft Speech Services",
                attribution=Attribution(
                    name="Microsoft",
                    url="https://azure.microsoft.com/en-us/products/ai-services/ai-speech",
                ),
                installed=True,
                version=speechsdk.__version__,
                models=[
                    AsrModel(
                        name="Standard",
                        description="Standard",
                        attribution=Attribution(
                            name="Microsoft",
                            url="https://azure.microsoft.com/en-us/products/ai-services/ai-speech/",
                        ),
                        installed=True,
                        languages=transcription_languages,
                        version=speechsdk.__version__,
                    ),
                ],
            ),
        ],
        tts=[
            TtsProgram(
                name="Azure AI Speech",
                description="Microsoft Speech Services",
                attribution=Attribution(
                    name="Microsoft",
                    url="https://azure.microsoft.com/en-us/products/ai-services/ai-speech",
                ),
                installed=True,
                version=speechsdk.__version__,
                voices=synthesization_voices,
            ),
        ],
    )


def get_transcription_languages(speech_service: SpeechService) -> list[str]:
    """Get list of languages available for transcription."""
    _LOGGER.info("Getting list of supported languages")
    try:
        transcription_languages = speech_service.transcription_languages
    except Exception:
        _LOGGER.exception("Failed getting list of supported languages")
        sys.exit(-1)
    _LOGGER.debug("Supported transcription languages: %s", transcription_languages)
    return transcription_languages


def get_synthesization_voices(speech_service: SpeechService) -> list[TtsVoice]:
    """Get list of voices available for synthesization."""
    _LOGGER.info("Getting list of supported voices")
    try:
        synthesization_voices = speech_service.synthesization_voices
    except Exception:
        _LOGGER.exception("Failed getting list of supported languages")
        sys.exit(-1)
    tts_voices = []
    for language, voices in synthesization_voices.items():
        tts_voices.extend(
            TtsVoice(
                name=voice["ShortName"],
                description=voice["DisplayName"],
                attribution=Attribution(
                    name="Microsoft",
                    url="https://azure.microsoft.com/en-us/products/ai-services/ai-speech/",
                ),
                installed=True,
                languages=[language],
                version=speechsdk.__version__,
            )
            for voice in voices
        )
    _LOGGER.debug("Supported synthesization voices: %s", tts_voices)
    return tts_voices


def run() -> None:
    """Run main process within asyncio."""
    asyncio.run(main())


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        run()
