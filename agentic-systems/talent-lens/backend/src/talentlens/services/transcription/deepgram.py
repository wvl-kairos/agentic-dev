"""Deepgram transcription service (fallback when Fireflies transcript is unavailable).

Used for:
- Async screening videos without Fireflies integration
- Re-transcription with better diarization
- Audio files uploaded manually
"""

import logging

logger = logging.getLogger(__name__)


async def transcribe_audio(audio_url: str) -> dict:
    """Transcribe audio via Deepgram API. Returns transcript with speaker diarization."""
    # TODO: call Deepgram API with diarization enabled
    # TODO: return {"transcript": str, "diarization": [...], "duration_seconds": int}
    raise NotImplementedError
