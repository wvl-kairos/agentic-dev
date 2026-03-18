"""Fireflies.ai webhook ingestion service.

Flow:
1. Webhook arrives with {meetingId, eventType}
2. Validate x-hub-signature (HMAC-SHA256)
3. Fetch full transcript via Fireflies GraphQL API
4. Parse sentences into diarization format
5. Create Interview record
"""

import hashlib
import hmac
import logging
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talentlens.config import settings
from talentlens.models.database.candidate import Candidate
from talentlens.models.database.interview import Interview, InterviewType

logger = logging.getLogger(__name__)

FIREFLIES_GRAPHQL_URL = "https://api.fireflies.ai/graphql"

TRANSCRIPT_QUERY = """
query Transcript($id: String!) {
  transcript(id: $id) {
    id
    title
    duration
    audio_url
    speakers {
      name
    }
    sentences {
      text
      speaker_name
      start_time
      end_time
    }
  }
}
"""


def validate_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validate Fireflies webhook HMAC-SHA256 signature."""
    if not secret:
        logger.warning("No webhook secret configured, skipping signature validation")
        return True
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


async def fetch_transcript(meeting_id: str) -> dict | None:
    """Fetch full transcript from Fireflies GraphQL API."""
    if not settings.fireflies_api_key:
        logger.warning("No Fireflies API key configured")
        return None

    async with httpx.AsyncClient() as client:
        response = await client.post(
            FIREFLIES_GRAPHQL_URL,
            json={"query": TRANSCRIPT_QUERY, "variables": {"id": meeting_id}},
            headers={"Authorization": f"Bearer {settings.fireflies_api_key}"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

    transcript = data.get("data", {}).get("transcript")
    if not transcript:
        logger.error("No transcript found for meeting %s", meeting_id)
        return None
    return transcript


def parse_diarization(sentences: list[dict]) -> list[dict]:
    """Convert Fireflies sentences to our diarization format."""
    return [
        {
            "speaker": s.get("speaker_name", "Unknown"),
            "text": s.get("text", ""),
            "start": s.get("start_time", 0),
            "end": s.get("end_time", 0),
        }
        for s in sentences
    ]


def build_full_transcript(sentences: list[dict]) -> str:
    """Build full transcript text from sentences."""
    lines = []
    for s in sentences:
        speaker = s.get("speaker_name", "Unknown")
        text = s.get("text", "")
        lines.append(f"{speaker}: {text}")
    return "\n".join(lines)


async def ingest_fireflies_transcript(
    meeting_id: str,
    candidate_id: uuid.UUID,
    interview_type: InterviewType,
    db: AsyncSession,
) -> Interview:
    """Fetch transcript from Fireflies and create Interview record."""
    transcript_data = await fetch_transcript(meeting_id)

    if transcript_data:
        sentences = transcript_data.get("sentences", [])
        diarization = parse_diarization(sentences)
        full_transcript = build_full_transcript(sentences)
        duration = transcript_data.get("duration")
    else:
        # Allow creating interview without Fireflies data (manual/test mode)
        diarization = []
        full_transcript = None
        duration = None

    recording_url = transcript_data.get("audio_url") if transcript_data else None

    interview = Interview(
        candidate_id=candidate_id,
        interview_type=interview_type,
        source="fireflies",
        external_id=meeting_id,
        transcript=full_transcript,
        diarization=diarization,
        recording_url=recording_url,
        duration_seconds=int(duration) if duration else None,
    )
    db.add(interview)
    await db.commit()
    await db.refresh(interview)

    logger.info(
        "Ingested interview %s from Fireflies meeting %s (%d segments)",
        interview.id,
        meeting_id,
        len(diarization),
    )
    return interview
