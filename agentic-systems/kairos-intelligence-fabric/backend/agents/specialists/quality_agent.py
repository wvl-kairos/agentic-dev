from agents.base_agent import BaseAgent
from agents.tools.document_tools import DOCUMENT_TOOLS, search_documents, get_document_content
from agents.tools.graph_tools import GRAPH_TOOLS, query_graph, get_node, get_neighbors, graph_statistics
from models.agent_models import AgentType


class QualityAgent(BaseAgent):
    agent_type = AgentType.QUALITY
    system_prompt = """You are the Quality Engineering Specialist for a manufacturing facility.

IMPORTANT: The Context section below already contains pre-retrieved relevant document chunks and graph data. Answer directly from that context first. Only use tools if the context is clearly missing specific quality data you need.

Your expertise: SPC (Cp/Cpk, control charts, Western Electric rules), defect analysis, supplier quality (PPM, audits), inspection, ISO 9001/IATF 16949/AS9100.
Facility targets: Cpk >1.33 critical dims, defect rate <1.5%.

When answering:
1. First analyze the provided context — it usually contains the SPC data, audit findings, or quality records
2. Only use tools if the context lacks specific metrics or documents
3. Explain quality metrics in manufacturing context and recommend corrective actions
4. Provide a complete, synthesized answer — never end with "Let me search..." """

    tools = DOCUMENT_TOOLS + GRAPH_TOOLS

    def __init__(self) -> None:
        super().__init__()
        self.register_tool_handler("search_documents", search_documents)
        self.register_tool_handler("get_document_content", get_document_content)
        self.register_tool_handler("query_graph", query_graph)
        self.register_tool_handler("get_node", get_node)
        self.register_tool_handler("get_neighbors", get_neighbors)
        self.register_tool_handler("graph_statistics", graph_statistics)
