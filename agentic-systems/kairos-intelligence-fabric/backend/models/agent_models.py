from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class AgentType(str, Enum):
    ONTOLOGY = "ontology"
    DOCUMENT = "document"
    ANALYTICS = "analytics"
    QUALITY = "quality"
    PROCESS = "process"


class ToolCall(BaseModel):
    name: str
    arguments: dict = {}


class ToolResult(BaseModel):
    tool_name: str
    result: str
    error: str | None = None


class AgentResponse(BaseModel):
    agent_type: AgentType
    response: str
    tool_calls: list[ToolCall] = []
    sources_used: list[str] = []
