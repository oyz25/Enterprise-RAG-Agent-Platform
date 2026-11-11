from typing import Dict, Any
from duckduckgo_search import DDGS
from app.tools.base import BaseTool


class WebSearchTool(BaseTool):
    """
    Tool for fetching real-time search results via DuckDuckGo.
    """

    name = "web_search"
    description = "Searches the web for real-time external information and news."

    def execute(self, query: str = "", max_results: int = 3, **kwargs) -> Dict[str, Any]:
        if not query.strip():
            return {"status": "error", "message": "Search query cannot be empty."}

        try:
            results = []
            with DDGS() as ddgs:
                ddg_results = ddgs.text(query, max_results=max_results)
                for r in ddg_results:
                    results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", "")
                    })

            return {
                "status": "success",
                "query": query,
                "total_results": len(results),
                "results": results
            }
        except Exception as e:
            return {"status": "error", "message": f"Web search failed: {str(e)}"}