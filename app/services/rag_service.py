import asyncio
import json
from typing import AsyncGenerator, Dict, Any, List
from app.services.vector_store import VectorStoreService


class RAGService:
    """
    Service for assembling retrieved context and generating RAG streaming responses.
    """

    def __init__(self):
        self.vector_store = VectorStoreService()

    def build_prompt(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Construct system prompt embedding retrieved context documents.
        """
        context_str = ""
        for idx, chunk in enumerate(context_chunks, start=1):
            filename = chunk.get("metadata", {}).get("filename", "unknown")
            context_str += f"\n--- Source Document {idx} (File: {filename}, Score: {chunk['score']}) ---\n{chunk['text']}\n"

        prompt = f"""You are an enterprise AI assistant answering questions based on the provided context documents.

CONTEXT DOCUMENTS:
{context_str}

USER QUESTION:
{query}

INSTRUCTIONS:
1. Answer the user question accurately using ONLY the provided context documents.
2. If the context does not contain enough information, state clearly that the information is not available in the knowledge base.
3. Keep the answer professional, clear, and structured.
"""
        return prompt

    async def generate_rag_stream(
        self, 
        query: str, 
        top_k: int = 3, 
        filename_filter: str = None
    ) -> AsyncGenerator[str, None]:
        """
        Retrieve chunks, assemble prompt, and stream answer chunks as SSE data.
        """
        # 1. Retrieve context chunks from Qdrant
        retrieved_chunks = self.vector_store.search_similarity(
            query_text=query,
            limit=top_k,
            filename_filter=filename_filter
        )

        # 2. Extract metadata citations
        citations = []
        for chunk in retrieved_chunks:
            citations.append({
                "chunk_id": chunk["chunk_id"],
                "filename": chunk.get("metadata", {}).get("filename", "unknown"),
                "score": chunk["score"],
                "text_snippet": chunk["text"][:150] + "..." if len(chunk["text"]) > 150 else chunk["text"]
            })

        # 3. Emit initial citations event
        yield f"data: {json.dumps({'event': 'citations', 'citations': citations})}\n\n"

        # 4. Construct Prompt
        full_prompt = self.build_prompt(query, retrieved_chunks)

        # 5. Simulate or Stream LLM response
        if not retrieved_chunks:
            response_text = "I could not find any relevant information in the knowledge base to answer your query."
        else:
            response_text = f"Based on the knowledge base documents ({', '.join(set(c['filename'] for c in citations))}):\n\n"
            response_text += f"The system analyzed the retrieved context for '{query}' and identified key matching data points.\n\n"
            response_text += f"Key Context Excerpt:\n> \"{retrieved_chunks[0]['text'][:300]}...\"\n\n"
            response_text += "The extracted records match your query criteria."

        # Stream text chunk by chunk for SSE
        words = response_text.split(" ")
        for word in words:
            chunk_payload = json.dumps({"event": "text", "delta": word + " "})
            yield f"data: {chunk_payload}\n\n"
            await asyncio.sleep(0.04)  # Simulate LLM token streaming delay

        # 6. Emit done event
        yield f"data: {json.dumps({'event': 'done'})}\n\n"