from agents.base_agent import BaseAgent
from agents.tools.analytics_tools import ANALYTICS_TOOLS, get_equipment_metrics, compare_equipment
from agents.tools.graph_tools import GRAPH_TOOLS, query_graph, get_node, get_neighbors, graph_statistics
from models.agent_models import AgentType


class AnalyticsAgent(BaseAgent):
    agent_type = AgentType.ANALYTICS
    system_prompt = """You are the Manufacturing Analytics Specialist.

IMPORTANT: The Context section below already contains pre-retrieved graph data and document chunks with equipment metrics. Answer directly from that context first. Only use tools if you need specific equipment metrics not already in the context.

OEE = Availability × Performance × Quality. Target: >82%.
Key metrics: OEE, utilization, MTBF, cycle times, defect rates, capacity.

When answering:
1. First analyze the provided context — it often contains the metrics you need
2. Only use tools if the context lacks specific equipment data
3. Calculate and explain OEE components, identify above/below target equipment
4. Provide a complete, synthesized answer — never end with "Let me look up..." """

    tools = ANALYTICS_TOOLS + GRAPH_TOOLS

    def __init__(self) -> None:
        super().__init__()
        self.register_tool_handler("get_equipment_metrics", get_equipment_metrics)
        self.register_tool_handler("compare_equipment", compare_equipment)
        self.register_tool_handler("query_graph", query_graph)
        self.register_tool_handler("get_node", get_node)
        self.register_tool_handler("get_neighbors", get_neighbors)
        self.register_tool_handler("graph_statistics", graph_statistics)
