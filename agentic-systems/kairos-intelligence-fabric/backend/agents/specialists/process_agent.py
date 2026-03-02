from agents.base_agent import BaseAgent
from agents.tools.analytics_tools import ANALYTICS_TOOLS, get_equipment_metrics, compare_equipment
from agents.tools.document_tools import DOCUMENT_TOOLS, search_documents, get_document_content
from agents.tools.graph_tools import GRAPH_TOOLS, query_graph, get_node, get_neighbors, graph_statistics
from models.agent_models import AgentType


class ProcessAgent(BaseAgent):
    agent_type = AgentType.PROCESS
    system_prompt = """You are the Process Optimization Specialist for a manufacturing facility.

IMPORTANT: The Context section below already contains pre-retrieved document chunks and graph data. Answer directly from that context first. Only use tools if the context is clearly missing specific process data you need.

Expertise: Lean (VSM, 7 wastes, 5S, Kaizen), production planning, PDCA, SMED, TPM.
Departments: Machining, Injection Molding, Assembly. KPIs: OEE, cycle time, throughput, FPY.

When answering:
1. First analyze the provided context — it often contains the process data you need
2. Only use tools if the context lacks specific details
3. Identify bottlenecks/waste, recommend actionable improvements, quantify impact
4. Provide a complete, synthesized answer — never end with "Let me search..." """

    tools = ANALYTICS_TOOLS + DOCUMENT_TOOLS + GRAPH_TOOLS

    def __init__(self) -> None:
        super().__init__()
        self.register_tool_handler("get_equipment_metrics", get_equipment_metrics)
        self.register_tool_handler("compare_equipment", compare_equipment)
        self.register_tool_handler("search_documents", search_documents)
        self.register_tool_handler("get_document_content", get_document_content)
        self.register_tool_handler("query_graph", query_graph)
        self.register_tool_handler("get_node", get_node)
        self.register_tool_handler("get_neighbors", get_neighbors)
        self.register_tool_handler("graph_statistics", graph_statistics)
