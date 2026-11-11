from typing import Dict, Any
from app.tools.base import BaseTool
from app.services.advanced_search_pipeline import AdvancedSearchPipelineService


class KnowledgeBaseTool(BaseTool):
    """
    Tool wrapping the Advanced RAG Search Pipeline for internal document retrieval.
    """

    name = "knowledge_base"
    description = "Queries the private vector database and executes hybrid search, reranking, and compression."

    def __init__(self):
        self.pipeline_service = AdvancedSearchPipelineService()

    def execute(self, query: str = "", top_k: int = 3, **kwargs) -> Dict[str, Any]:
        if not query.strip():
            return {"status": "error", "message": "Query cannot be empty."}

        try:
            output = self.pipeline_service.execute_pipeline(
                query=query,
                top_k=top_k,
                enable_rerank=True,
                enable_compression=True
            )
            return {
                "status": "success",
                "query": query,
                "stages_executed": output["pipeline_stages_executed"],
                "results": output["results"]
            }
        except Exception as e:
            return {"status": "error", "message": f"Knowledge base lookup failed: {str(e)}"}