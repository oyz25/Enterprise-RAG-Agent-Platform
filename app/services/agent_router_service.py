from typing import Dict, Any, Tuple
from app.schemas.agent import AgentIntent
from app.tools.registry import ToolRegistry
from app.tools.calculator_tool import CalculatorTool
from app.tools.web_search_tool import WebSearchTool
from app.tools.knowledge_base_tool import KnowledgeBaseTool


class AgentRouterService:
    """
    Multi-Agent Router Service responsible for classifying user intent 
    and dynamically executing tools registered in ToolRegistry.
    """

    def __init__(self):
        self.registry = ToolRegistry()

        # Register available tools
        self.registry.register_tool(CalculatorTool())
        self.registry.register_tool(WebSearchTool())
        self.registry.register_tool(KnowledgeBaseTool())

    def classify_intent(self, query: str) -> Tuple[AgentIntent, float, str]:
        """
        Classify query intent using pattern matching.
        """
        clean_query = query.lower().strip()

        # 1. Calculator intent pattern
        if any(op in clean_query for op in ["+", "-", "*", "/", "calc", "calculate"]):
            return AgentIntent.CALCULATOR, 0.95, "Query contains mathematical calculation instructions."

        # 2. Web search intent pattern
        if any(kw in clean_query for kw in ["latest news", "today", "weather", "search web", "realtime", "live"]):
            return AgentIntent.WEB_SEARCH, 0.90, "Query requests real-time external web information."

        # 3. Direct chat pattern
        if any(clean_query.startswith(kw) for kw in ["hi", "hello", "hey", "who are you", "what can you do"]):
            return AgentIntent.DIRECT_CHAT, 0.98, "Query is a conversational greeting or general capability question."

        # 4. Default to Knowledge Base RAG Search
        return AgentIntent.KNOWLEDGE_BASE, 0.85, "Query requires context retrieval from internal knowledge base."

    def route_and_execute(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Route intent to ToolRegistry and execute registered tool.
        """
        intent, confidence, reasoning = self.classify_intent(query)

        if intent == AgentIntent.KNOWLEDGE_BASE:
            result_data = self.registry.execute_tool("knowledge_base", query=query)
            action = "Executed Tool: knowledge_base (Advanced RAG Pipeline)"

        elif intent == AgentIntent.CALCULATOR:
            result_data = self.registry.execute_tool("calculator", expression=query)
            action = "Executed Tool: calculator"

        elif intent == AgentIntent.WEB_SEARCH:
            result_data = self.registry.execute_tool("web_search", query=query)
            action = "Executed Tool: web_search (DuckDuckGo Search Engine)"

        else:  # DIRECT_CHAT
            available_tools = self.registry.list_tools()
            result_data = {
                "response": "Hello! I am your Enterprise RAG AI Assistant. How can I assist you today?",
                "available_tools": available_tools
            }
            action = "Executed Conversational Handler"

        return {
            "intent": intent,
            "confidence_score": confidence,
            "reasoning": reasoning,
            "executed_action": action,
            "result": result_data
        }