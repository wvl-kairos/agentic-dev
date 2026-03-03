"""Talk ratio calculation from diarized transcripts.

Measures the proportion of interview time where the candidate is speaking.
Candidates should dominate conversation time in a good interview.
"""


def compute_talk_ratio(diarization: list[dict]) -> float:
    """Compute candidate talk ratio from speaker-labeled segments.

    Args:
        diarization: List of {"speaker": str, "start": float, "end": float, "text": str}

    Returns:
        Float between 0.0 and 1.0 representing candidate's share of total talk time.
    """
    # TODO: identify candidate speaker (heuristic: not the interviewer)
    # TODO: sum durations per speaker
    # TODO: return candidate_duration / total_duration
    raise NotImplementedError
