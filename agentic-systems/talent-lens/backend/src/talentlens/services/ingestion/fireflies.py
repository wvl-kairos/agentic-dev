"""Fireflies.ai webhook ingestion service.

Handles:
- Webhook signature validation
- Transcript extraction from Fireflies payload
- Speaker diarization parsing
- Interview record creation
"""

import logging

logger = logging.getLogger(__name__)


async def validate_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Validate Fireflies webhook HMAC signature."""
    # TODO: implement HMAC-SHA256 validation
    raise NotImplementedError


async def ingest_fireflies_transcript(payload: dict) -> dict:
    """Parse Fireflies webhook payload, extract transcript and diarization,
    create Interview record, and return interview_id for pipeline processing."""
    # TODO: extract meeting_id, transcript, speakers, duration
    # TODO: create Interview record with diarization JSON
    raise NotImplementedError
