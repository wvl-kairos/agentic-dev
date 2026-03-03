"""Talk ratio calculation from diarized transcripts.

Measures the proportion of interview time where the candidate is speaking.
Candidates should dominate conversation time in a good interview.

Heuristic for identifying the candidate:
- The candidate is the speaker who is NOT the most frequent short-turn speaker
  (interviewers tend to ask short questions, candidates give long answers)
- If we can't determine, we pick the speaker with the most total talk time
  (candidates should be talking more in a well-run interview)
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def _speaker_stats(diarization: list[dict]) -> dict[str, dict]:
    """Compute per-speaker statistics from diarization segments."""
    stats: dict[str, dict] = defaultdict(lambda: {"duration": 0.0, "segments": 0, "chars": 0})
    for seg in diarization:
        speaker = seg.get("speaker", "Unknown")
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        text = seg.get("text", "")
        duration = max(0, end - start)
        stats[speaker]["duration"] += duration
        stats[speaker]["segments"] += 1
        stats[speaker]["chars"] += len(text)
    return dict(stats)


def identify_candidate_speaker(diarization: list[dict], candidate_name: str | None = None) -> str:
    """Identify which speaker is the candidate.

    Strategy:
    1. If candidate_name is provided, fuzzy match against speaker names
    2. Otherwise, the candidate is the speaker with the longest avg segment duration
       (candidates give long answers, interviewers ask short questions)
    """
    stats = _speaker_stats(diarization)
    if not stats:
        return "Unknown"

    # Try name matching first
    if candidate_name:
        name_lower = candidate_name.lower()
        for speaker in stats:
            if name_lower in speaker.lower() or speaker.lower() in name_lower:
                logger.info("Matched candidate speaker by name: %s", speaker)
                return speaker

    # Heuristic: candidate has highest avg chars per segment (longer answers)
    avg_chars = {
        speaker: s["chars"] / max(s["segments"], 1) for speaker, s in stats.items()
    }
    candidate = max(avg_chars, key=avg_chars.get)
    logger.info(
        "Identified candidate speaker by heuristic: %s (avg %d chars/segment)",
        candidate,
        avg_chars[candidate],
    )
    return candidate


def compute_talk_ratio(
    diarization: list[dict], candidate_name: str | None = None
) -> dict:
    """Compute talk ratio from diarization segments.

    Returns:
        {
            "candidate_speaker": str,
            "candidate_ratio": float,  # 0.0 - 1.0
            "speaker_durations": {speaker: seconds},
            "total_duration": float,
        }
    """
    if not diarization:
        return {
            "candidate_speaker": "Unknown",
            "candidate_ratio": 0.0,
            "speaker_durations": {},
            "total_duration": 0.0,
        }

    stats = _speaker_stats(diarization)
    candidate_speaker = identify_candidate_speaker(diarization, candidate_name)

    total_duration = sum(s["duration"] for s in stats.values())
    if total_duration == 0:
        # Fall back to character count ratio
        total_chars = sum(s["chars"] for s in stats.values())
        candidate_ratio = (
            stats.get(candidate_speaker, {}).get("chars", 0) / max(total_chars, 1)
        )
    else:
        candidate_ratio = stats.get(candidate_speaker, {}).get("duration", 0) / total_duration

    speaker_durations = {speaker: s["duration"] for speaker, s in stats.items()}

    return {
        "candidate_speaker": candidate_speaker,
        "candidate_ratio": round(candidate_ratio, 3),
        "speaker_durations": speaker_durations,
        "total_duration": total_duration,
    }
