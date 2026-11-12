import os
from typing import List, Dict, Any, Tuple
import httpx
from app.schemas.agent import AgentIntent


class LLMSynthesizerService:
    """
    Synthesizes citation-grounded natural language answers from retrieved context,
    tool outputs, and multi-turn conversation history.
    """

    def __init__(self):
        self.base_url = os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
        self.api_key = os.getenv("LLM_API_KEY", "ollama")
        self.model = os.getenv("LLM_MODEL", "llama3.2")
        self.enabled = os.getenv("LLM_ENABLED", "true").lower() == "true"

    def _build_numbered_sources(
        self, intent: AgentIntent, result_data: Dict[str, Any]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Normalize tool outputs into numbered [Source N] blocks and structured citation metadata.
        """
        citations: List[Dict[str, Any]] = []
        source_blocks: List[str] = []

        if intent == AgentIntent.KNOWLEDGE_BASE:
            items = result_data.get("results", [])
            for idx, item in enumerate(items, start=1):
                text = (item.get("compressed_text") or item.get("text", "")).strip()
                score = item.get("relevance_score", item.get("rrf_score", 0.0))
                chunk_id = item.get("chunk_id", f"chunk-{idx}")
                citations.append({
                    "source_number": idx,
                    "type": "knowledge_base",
                    "chunk_id": chunk_id,
                    "relevance_score": score,
                    "snippet": text,
                })
                source_blocks.append(f"[Source {idx}] (Chunk ID: {chunk_id}, Relevance: {score}):\n{text}")

        elif intent == AgentIntent.WEB_SEARCH:
            items = result_data.get("results", [])
            for idx, item in enumerate(items, start=1):
                title = item.get("title", "Web Result")
                snippet = item.get("snippet", "").strip()
                url = item.get("url", "")
                citations.append({
                    "source_number": idx,
                    "type": "web_search",
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                })
                source_blocks.append(f"[Source {idx}] ({title} - {url}):\n{snippet}")

        return "\n\n".join(source_blocks), citations

    def _call_openai_compatible_llm(
        self,
        query: str,
        context_block: str,
        history: List[Dict[str, Any]],
    ) -> str:
        """
        Send grounded synthesis prompt to any OpenAI-compatible chat completions API.
        """
        system_prompt = (
            "You are an Enterprise RAG AI Assistant. Synthesize a clear, accurate, and concise "
            "answer to the user's prompt using ONLY the provided numbered sources and conversation history. "
            "Cite every factual claim inline using [Source 1], [Source 2], etc. "
            "Never invent information not present in the sources. If the sources do not contain enough "
            "information to answer the prompt, state that explicitly."
        )

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # Inject recent prior turns for multi-turn awareness
        for turn in history[-4:]:
            role = turn.get("role")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

        user_prompt = (
            f"Retrieved Context:\n{context_block}\n\n"
            f"User Question: {query}\n\n"
            "Provide a grounded answer with inline [Source N] citations:"
        )
        messages.append({"role": "user", "content": user_prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        with httpx.Client(timeout=12.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    def _extractive_grounded_fallback(
        self,
        intent: AgentIntent,
        result_data: Dict[str, Any],
        citations: List[Dict[str, Any]],
    ) -> str:
        """
        Deterministic citation-grounded synthesis when no local/external LLM server is reachable.
        """
        if intent == AgentIntent.CALCULATOR:
            if result_data.get("status") == "error":
                return f"Calculation error: {result_data.get('message', 'Invalid expression')}"
            return f"The evaluated result of `{result_data.get('expression')}` is **{result_data.get('result')}**."

        if intent == AgentIntent.DIRECT_CHAT:
            return str(result_data.get("response", "Hello! How can I assist you today?"))

        if not citations:
            return "I searched the available sources, but found no matching records to answer your query."

        summary_lines = ["Based on the retrieved context, here is the grounded answer:\n"]
        for c in citations:
            num = c["source_number"]
            snippet = c["snippet"]
            if c["type"] == "web_search":
                summary_lines.append(f"- **{c['title']}**: {snippet} [Source {num}]")
            else:
                summary_lines.append(f"- {snippet} [Source {num}]")

        return "\n".join(summary_lines)

    def synthesize(
        self,
        query: str,
        intent: AgentIntent,
        result_data: Dict[str, Any],
        history: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """
        Generate final answer with citation metadata and synthesis mode indicator.
        """
        history = history or []
        context_block, citations = self._build_numbered_sources(intent, result_data)

        # Deterministic intents (Calculator / Direct Chat) skip external LLM overhead
        if intent in (AgentIntent.CALCULATOR, AgentIntent.DIRECT_CHAT) or not citations:
            answer = self._extractive_grounded_fallback(intent, result_data, citations)
            mode = "extractive_grounded"
        else:
            mode = "extractive_grounded"
            answer = ""
            if self.enabled:
                try:
                    answer = self._call_openai_compatible_llm(query, context_block, history)
                    mode = f"llm_grounded ({self.model})"
                except Exception:
                    answer = self._extractive_grounded_fallback(intent, result_data, citations)
            else:
                answer = self._extractive_grounded_fallback(intent, result_data, citations)

        # Append structured References block when citations exist
        if citations:
            ref_lines = ["\n\n**References:**"]
            for c in citations:
                if c["type"] == "web_search":
                    ref_lines.append(f"- **[Source {c['source_number']}]** {c['title']} ({c['url']})")
                else:
                    ref_lines.append(
                        f"- **[Source {c['source_number']}]** Chunk `{c['chunk_id']}` (Relevance: {c['relevance_score']})"
                    )
            answer = answer + "\n".join(ref_lines)

        return {
            "answer": answer,
            "citations": citations,
            "synthesis_mode": mode,
        }