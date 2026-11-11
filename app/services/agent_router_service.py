import re
from typing import Dict, Any, Tuple
from app.schemas.agent import AgentIntent
from app.services.advanced_search_pipeline import AdvancedSearchPipelineService


class AgentRouterService:
    """
    Multi-Agent Router Service responsible for classifying user intent 
    and routing tasks to specialized sub-agents or tool pipelines.
    """

    def __init__(self):
        self.search_pipeline = AdvancedSearchPipelineService()

    def classify_intent(self, query: str) -> Tuple[AgentIntent, float, str]:
        """
        Classify query intent using heuristic rules and pattern matching.
        """
        clean_query = query.lower().strip()

        # 1. Calculator intent pattern
        if re.search(r"[\d\s\+\-\*\/\(\)\%]+", clean_query) and any(op in clean_query for op in ["+", "-", "*", "/", "calc", "calculate"]):
            return AgentIntent.CALCULATOR, 0.95, "Query contains mathematical calculation instructions."

        # 2. Web search intent pattern
        if any(kw in clean_query for kw in ["latest news", "today", "weather", "search web", "realtime", "live"]):
            return AgentIntent.WEB_SEARCH, 0.90, "Query requests real-time external web information."

        # 3. Direct chat pattern
        if any(clean_query.startswith(kw) for kw in ["hi", "hello", "hey", "who are you", "what can you do", "thanks"]):
            return AgentIntent.DIRECT_CHAT, 0.98, "Query is a conversational greeting or general capability question."

        # 4. Default to Knowledge Base RAG Search
        return AgentIntent.KNOWLEDGE_BASE, 0.85, "Query requires context retrieval from internal knowledge base."

    def route_and_execute(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Route intent to corresponding handler and return execution results.
        """
        intent, confidence, reasoning = self.classify_intent(query)
        
        if intent == AgentIntent.KNOWLEDGE_BASE:
            pipeline_result = self.search_pipeline.execute_pipeline(
                query=query,
                top_k=3,
                enable_rerank=True,
                enable_compression=True
            )
            action = "Executed Advanced RAG Search Pipeline (Hybrid + Reranker + Compression)"
            result_data = pipeline_result

        elif intent == AgentIntent.CALCULATOR:
            try:
                expr = re.sub(r"[^\d\+\-\*\/\(\)\.]", "", query)
                val = eval(expr)
                result_data = {"expression": expr, "result": val}
                action = "Executed Math Calculator Tool"
            except Exception:
                result_data = {"error": "Failed to evaluate mathematical expression."}
                action = "Failed Calculator Execution"

        elif intent == AgentIntent.WEB_SEARCH:
            result_data = {"message": "Web search query queued for external tool agent."}
            action = "Delegated to Web Search Agent"

        else:  # DIRECT_CHAT
            result_data = {"response": "Hello! I am your Enterprise RAG AI Assistant. How can I assist you today?"}
            action = "Executed Conversational Handler"

        return {
            "intent": intent,
            "confidence_score": confidence,
            "reasoning": reasoning,
            "executed_action": action,
            "result": result_data
        }