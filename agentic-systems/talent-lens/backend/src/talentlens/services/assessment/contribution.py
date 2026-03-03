"""Individual contribution detection.

Distinguishes between "I built/designed/implemented" (individual) vs
"we built/our team" (collective) statements. Helps assess whether
candidates can articulate their personal impact.

Supports both English and Spanish patterns for LATAM candidates.
"""

import re
from dataclasses import dataclass, field

# Patterns: (regex, type)
# We match at word boundaries to avoid false positives inside longer words
INDIVIDUAL_PATTERNS = [
    # English
    r"\bI\s+(?:built|designed|implemented|created|developed|led|architected|wrote|shipped|owned|managed|drove|initiated|proposed|decided)\b",
    r"\bmy\s+(?:approach|solution|design|implementation|decision|idea|contribution|role|responsibility)\b",
    r"\bI\s+was\s+(?:responsible|accountable|the\s+lead|in\s+charge)\b",
    # Spanish
    r"\byo\s+(?:construí|diseñé|implementé|creé|desarrollé|lideré|escribí|propuse|decidí)\b",
    r"\bmi\s+(?:enfoque|solución|diseño|implementación|decisión|idea|contribución|rol)\b",
]

COLLECTIVE_PATTERNS = [
    # English
    r"\bwe\s+(?:built|designed|implemented|created|developed|decided|shipped|launched|deployed)\b",
    r"\b(?:our|the)\s+team\s+(?:built|designed|implemented|created|developed|decided)\b",
    r"\bas\s+a\s+team\b",
    r"\bteam\s+effort\b",
    # Spanish
    r"\bnosotros\s+(?:construimos|diseñamos|implementamos|creamos|desarrollamos|decidimos)\b",
    r"\b(?:nuestro|el)\s+equipo\b",
]


@dataclass
class ContributionResult:
    individual_count: int = 0
    collective_count: int = 0
    ratio: float = 0.0
    examples: list[dict] = field(default_factory=list)


def detect_contributions(transcript: str, candidate_speaker: str | None = None) -> dict:
    """Analyze transcript for individual vs collective contribution signals.

    Args:
        transcript: Full transcript text (speaker-labeled lines)
        candidate_speaker: If provided, only analyze lines from this speaker

    Returns:
        {
            "individual_count": int,
            "collective_count": int,
            "ratio": float,  # individual / (individual + collective), 0.0-1.0
            "examples": [{"text": str, "type": "individual"|"collective", "pattern": str}]
        }
    """
    if not transcript:
        return ContributionResult().__dict__

    # Filter to candidate lines if speaker is known
    lines = transcript.split("\n")
    if candidate_speaker:
        lines = [
            line for line in lines
            if line.lower().startswith(candidate_speaker.lower() + ":")
        ]
    text = "\n".join(lines)

    result = ContributionResult()

    # Find individual contribution signals
    for pattern in INDIVIDUAL_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            result.individual_count += 1
            # Extract context (surrounding sentence)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 100)
            context = text[start:end].strip()
            # Clean up to sentence boundary
            if start > 0:
                context = "..." + context
            result.examples.append({
                "text": context,
                "type": "individual",
                "pattern": match.group(),
            })

    # Find collective contribution signals
    for pattern in COLLECTIVE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            result.collective_count += 1
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 100)
            context = text[start:end].strip()
            if start > 0:
                context = "..." + context
            result.examples.append({
                "text": context,
                "type": "collective",
                "pattern": match.group(),
            })

    total = result.individual_count + result.collective_count
    result.ratio = result.individual_count / max(total, 1)

    # Cap examples to avoid bloat
    result.examples = result.examples[:20]

    return {
        "individual_count": result.individual_count,
        "collective_count": result.collective_count,
        "ratio": round(result.ratio, 3),
        "examples": result.examples,
    }
