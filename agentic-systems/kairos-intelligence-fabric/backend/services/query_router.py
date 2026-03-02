from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Keyword-based routing (avoids extra LLM call for simple cases)
GRAPH_KEYWORDS = {
    "connected", "relationship", "neighbors", "linked", "path",
    "between", "network", "graph", "related to", "connections",
}
DOC_KEYWORDS = {
    "document", "report", "manual", "specification", "procedure",
    "policy", "audit", "training", "certification", "safety",
    "incident", "kaizen", "maintenance", "bom", "bill of materials",
    "spc", "cpk",
}
ANALYTICS_KEYWORDS = {
    "oee", "trend", "performance", "metrics", "kpi", "utilization",
    "efficiency", "downtime", "yield", "defect rate", "capacity",
    "mtbf", "cycle time", "throughput", "cpk", "spc",
}


def classify_query(query: str) -> str:
    """Classify query intent based on keywords.

    Returns one of: graph_lookup, document_search, analytical, hybrid
    """
    q_lower = query.lower()

    graph_score = sum(1 for kw in GRAPH_KEYWORDS if kw in q_lower)
    doc_score = sum(1 for kw in DOC_KEYWORDS if kw in q_lower)
    analytics_score = sum(1 for kw in ANALYTICS_KEYWORDS if kw in q_lower)

    # If clear winner, use it
    scores = {
        "graph_lookup": graph_score,
        "document_search": doc_score,
        "analytical": analytics_score,
    }
    max_score = max(scores.values())

    if max_score >= 2:
        winners = [k for k, v in scores.items() if v == max_score]
        if len(winners) == 1:
            return winners[0]

    # Entity reference pattern -> graph-oriented but hybrid
    entity_pattern = re.compile(r"(CNC|lathe|line|supplier|product|order|equip)", re.IGNORECASE)
    if entity_pattern.search(query):
        if analytics_score > 0:
            return "analytical"
        return "hybrid"

    # Default to hybrid
    return "hybrid"
