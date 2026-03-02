from __future__ import annotations

from typing import Any

CRYSTALLIZATION_TOOLS = [
    {
        "name": "save_insight",
        "description": "Save an important insight or finding to the knowledge graph. Use this when you discover something noteworthy that should be preserved for future reference.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The insight or finding to save",
                },
                "related_entity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs of entities this insight relates to",
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence level 0-1 (default 0.8)",
                },
            },
            "required": ["content", "related_entity_ids"],
        },
    },
]


async def save_insight_tool(
    content: str,
    related_entity_ids: list[str],
    confidence: float = 0.8,
    agent_name: str = "",
    query: str = "",
) -> dict[str, Any]:
    from services.crystallization_service import save_insight

    return await save_insight(
        content=content,
        related_entity_ids=related_entity_ids,
        confidence=confidence,
        agent_name=agent_name,
        query=query,
    )
