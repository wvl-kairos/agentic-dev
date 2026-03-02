from agents.base_agent import BaseAgent
from agents.tools.document_tools import DOCUMENT_TOOLS, search_documents, get_document_content
from agents.tools.graph_tools import GRAPH_TOOLS, query_graph, get_node, get_neighbors, graph_statistics
from models.agent_models import AgentType


class DocumentAgent(BaseAgent):
    agent_type = AgentType.DOCUMENT
    system_prompt = """You are the Document Analysis Specialist for a manufacturing facility.

IMPORTANT: The Context section below already contains pre-retrieved relevant document chunks and graph data. Answer directly from that context first. Only use tools if the context is clearly missing information you need.

When answering:
1. First analyze the provided context — it usually has the answer
2. Only use search_documents or get_document_content if the context lacks specific details
3. Quote specific data points and reference document IDs
4. If the information is NOT found in any document, clearly state that
5. NEVER end with narration like "Let me search..." or "Let me look up..." — always give a complete answer """

    tools = DOCUMENT_TOOLS + GRAPH_TOOLS

    def __init__(self) -> None:
        super().__init__()
        self.register_tool_handler("search_documents", search_documents)
        self.register_tool_handler("get_document_content", get_document_content)
        self.register_tool_handler("query_graph", query_graph)
        self.register_tool_handler("get_node", get_node)
        self.register_tool_handler("get_neighbors", get_neighbors)
        self.register_tool_handler("graph_statistics", graph_statistics)
