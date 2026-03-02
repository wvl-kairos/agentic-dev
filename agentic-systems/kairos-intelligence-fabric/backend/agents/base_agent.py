from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from config import settings
from models.agent_models import AgentResponse, AgentType

logger = logging.getLogger(__name__)

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def _is_narration(text: str) -> bool:
    """Detect responses that are narration/planning rather than real answers.

    E.g. "Let me search for...", "I'll look up...", ending with ":"
    """
    stripped = text.strip()
    # Ends with colon — agent was about to do something but stopped
    if stripped.endswith(":"):
        return True
    # Very short and starts with planning language
    if len(stripped) < 120:
        lower = stripped.lower()
        narration_starts = (
            "let me search", "let me look", "let me find", "let me check",
            "i'll search", "i'll look", "i'll find", "i'll check",
            "i will search", "i will look", "searching for",
        )
        if any(lower.startswith(p) for p in narration_starts):
            return True
    return False


class BaseAgent:
    """Base class for all specialist agents."""

    agent_type: AgentType
    system_prompt: str = ""
    tools: list[dict[str, Any]] = []

    def __init__(self) -> None:
        self._tool_handlers: dict[str, Any] = {}

    def register_tool_handler(self, name: str, handler: Any) -> None:
        self._tool_handlers[name] = handler

    async def process(
        self,
        query: str,
        context: str,
        history: list[dict[str, str]] | None = None,
    ) -> AgentResponse:
        """Process a query with retrieved context using Claude.

        The query pipeline already retrieves relevant context (graph + RAG).
        Tools are available for the agent to fetch *additional* details only
        when the pre-retrieved context is insufficient.  The tool loop is
        capped at 3 rounds to keep latency under control (~6-15 s total).
        """
        if not settings.anthropic_api_key:
            return AgentResponse(
                agent_type=self.agent_type,
                response=f"[{self.agent_type.value} agent] API key not configured. Context:\n{context}",
            )

        client = _get_client()

        # Build messages: include conversation history for multi-turn awareness
        messages: list[dict] = []
        if history:
            for h in history[-10:]:
                role = h.get("role", "user")
                content = h.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        messages.append(
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}",
            }
        )

        try:
            # Make initial call
            response = await client.messages.create(
                model=settings.agent_model,
                max_tokens=8192,
                temperature=settings.agent_temperature,
                system=self.system_prompt,
                messages=messages,
                tools=self.tools if self.tools else anthropic.NOT_GIVEN,
            )

            # Handle tool use loop (max 3 rounds — keep latency low)
            sources_used: list[str] = []
            for round_num in range(3):
                if response.stop_reason != "tool_use":
                    break

                # Process tool calls
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self._execute_tool(block.name, block.input)
                        sources_used.append(block.name)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

                # On the last allowed round, drop tools so Claude MUST
                # respond with text instead of requesting more tool calls.
                provide_tools = round_num < 2
                response = await client.messages.create(
                    model=settings.agent_model,
                    max_tokens=8192,
                    temperature=settings.agent_temperature,
                    system=self.system_prompt,
                    messages=messages,
                    tools=(self.tools if provide_tools else anthropic.NOT_GIVEN),
                )

            # Safety net: if still tool_use after the loop (shouldn't happen
            # because round 3 already drops tools, but just in case)
            if response.stop_reason == "tool_use":
                logger.warning(
                    "Agent %s still requesting tools after loop — forcing summary",
                    self.agent_type.value,
                )
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await self._execute_tool(block.name, block.input)
                        sources_used.append(block.name)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "assistant", "content": response.content})
                tool_results.append({
                    "type": "text",
                    "text": "Please provide your final answer now based on all the information gathered.",
                })
                messages.append({"role": "user", "content": tool_results})
                response = await client.messages.create(
                    model=settings.agent_model,
                    max_tokens=8192,
                    temperature=settings.agent_temperature,
                    system=self.system_prompt,
                    messages=messages,
                )

            # Extract text response
            text_parts = [b.text for b in response.content if hasattr(b, "text")]
            response_text = "\n".join(text_parts).strip()

            # Detect incomplete narration responses (agent said "Let me search..."
            # instead of giving a real answer)
            if response_text and _is_narration(response_text):
                logger.warning(
                    "Agent %s returned narration instead of answer: %s...",
                    self.agent_type.value, response_text[:80],
                )
                response_text = ""

            if not response_text:
                logger.warning(
                    "Agent %s returned empty text (stop_reason=%s)",
                    self.agent_type.value, response.stop_reason,
                )
                response_text = ""

            return AgentResponse(
                agent_type=self.agent_type,
                response=response_text,
                sources_used=sources_used,
            )

        except Exception as e:
            logger.error("Agent %s failed: %s", self.agent_type.value, e)
            return AgentResponse(
                agent_type=self.agent_type,
                response=f"I encountered an error processing your request: {e}",
            )

    async def _execute_tool(self, name: str, arguments: dict) -> str:
        """Execute a registered tool and return the result."""
        handler = self._tool_handlers.get(name)
        if not handler:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            result = await handler(**arguments)
            return json.dumps(result) if isinstance(result, (dict, list)) else str(result)
        except Exception as e:
            return json.dumps({"error": str(e)})
