from __future__ import annotations

import asyncio
import logging

from agents.specialists.analytics_agent import AnalyticsAgent
from agents.specialists.document_agent import DocumentAgent
from agents.specialists.ontology_agent import OntologyAgent
from agents.specialists.process_agent import ProcessAgent
from agents.specialists.quality_agent import QualityAgent
from models.agent_models import AgentResponse, AgentType

logger = logging.getLogger(__name__)

# Agent instances (lazy init)
_agents: dict[AgentType, object] | None = None


def _get_agents() -> dict[AgentType, object]:
    global _agents
    if _agents is None:
        _agents = {
            AgentType.ONTOLOGY: OntologyAgent(),
            AgentType.DOCUMENT: DocumentAgent(),
            AgentType.ANALYTICS: AnalyticsAgent(),
            AgentType.QUALITY: QualityAgent(),
            AgentType.PROCESS: ProcessAgent(),
        }
    return _agents


def select_agents(query: str, mode: str) -> list[AgentType]:
    """Select which agents should handle this query based on content and mode."""
    q_lower = query.lower()
    selected: list[AgentType] = []

    # Mode-based primary selection
    if mode == "graph_lookup":
        selected.append(AgentType.ONTOLOGY)
    elif mode == "document_search":
        selected.append(AgentType.DOCUMENT)
    elif mode == "analytical":
        selected.append(AgentType.ANALYTICS)

    # Content-based secondary selection
    quality_terms = {"quality", "defect", "spc", "cpk", "inspection", "audit", "supplier quality"}
    process_terms = {"kaizen", "lean", "bottleneck", "cycle time", "capacity", "improvement", "waste", "schedule"}
    analytics_terms = {"oee", "mtbf", "utilization", "performance", "metric", "trend"}
    document_terms = {"document", "report", "manual", "procedure", "training", "certification"}

    if any(t in q_lower for t in quality_terms) and AgentType.QUALITY not in selected:
        selected.append(AgentType.QUALITY)
    if any(t in q_lower for t in process_terms) and AgentType.PROCESS not in selected:
        selected.append(AgentType.PROCESS)
    if any(t in q_lower for t in analytics_terms) and AgentType.ANALYTICS not in selected:
        selected.append(AgentType.ANALYTICS)
    if any(t in q_lower for t in document_terms) and AgentType.DOCUMENT not in selected:
        selected.append(AgentType.DOCUMENT)

    # Default: ontology + document for hybrid queries
    if not selected:
        selected = [AgentType.ONTOLOGY, AgentType.DOCUMENT]

    # Limit to 2 agents
    return selected[:2]


async def process_with_agents(
    query: str,
    context: str,
    mode: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """Route query to selected specialists and synthesize responses."""
    agent_types = select_agents(query, mode)
    agents = _get_agents()

    logger.info("Selected agents: %s", [a.value for a in agent_types])

    # Run selected agents in parallel
    tasks = []
    for agent_type in agent_types:
        agent = agents[agent_type]
        tasks.append(agent.process(query, context, history=history))

    responses: list[AgentResponse] = await asyncio.gather(*tasks)

    # Synthesize responses — filter out empty ones
    valid_responses = [r for r in responses if r.response]

    if len(valid_responses) == 0:
        return (
            "I could not find the entities or information you're asking about in the "
            "knowledge graph or documents. This may mean the entity doesn't exist in "
            "the current dataset, or it might be referenced by a different name. "
            "Try asking about a specific entity you can see in the graph, or upload "
            "documents containing the information you need."
        )

    if len(valid_responses) == 1:
        return valid_responses[0].response

    # Multiple agents: combine their responses
    parts = []
    for resp in valid_responses:
        agent_label = resp.agent_type.value.title()
        parts.append(f"**{agent_label} Analysis:**\n{resp.response}")

    return "\n\n---\n\n".join(parts)
