import re
from typing import List, Dict, Any
from app.services.chunking_engine import ChunkingEngine


class ContextCompressorService:
    """
    Service for filtering low-relevance noise and extracting key sentences from retrieved chunks.
    """

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """
        Split a block of text into individual sentence strings using regex.
        """
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def compress_chunk(self, query: str, chunk_text: str) -> str:
        """
        Extract sentences from chunk_text that share key terms with the query.
        """
        sentences = self.split_into_sentences(chunk_text)
        if len(sentences) <= 1:
            return chunk_text

        query_words = set(re.sub(r"[^\w\s]", "", query.lower()).split())
        
        relevant_sentences = []
        for sentence in sentences:
            sentence_words = set(re.sub(r"[^\w\s]", "", sentence.lower()).split())
            # Keep sentence if it shares keywords with the query
            if query_words.intersection(sentence_words):
                relevant_sentences.append(sentence)

        # Fallback to original text if word intersection yields nothing
        if not relevant_sentences:
            return sentences[0]

        return " ".join(relevant_sentences)

    def process_compression(
        self, 
        query: str, 
        chunks: List[Dict[str, Any]], 
        min_score_threshold: float = 0.0,
        max_tokens: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Filter out low-scoring chunks and compress sentence content within token budget.
        """
        compressed_results = []
        accumulated_tokens = 0

        for chunk in chunks:
            score = chunk.get("relevance_score", chunk.get("score", 0.0))

            # 1. Noise Filtering: Skip items below score threshold
            if score < min_score_threshold:
                continue

            raw_text = chunk.get("text", "")
            original_tokens = ChunkingEngine.count_tokens(raw_text)

            # 2. Sentence-level compression
            compressed_text = self.compress_chunk(query, raw_text)
            compressed_tokens = ChunkingEngine.count_tokens(compressed_text)

            # Check if adding this chunk exceeds max token budget
            if accumulated_tokens + compressed_tokens > max_tokens and compressed_results:
                break

            accumulated_tokens += compressed_tokens
            reduction_ratio = round((1 - (compressed_tokens / max(original_tokens, 1))) * 100, 2)

            compressed_results.append({
                "chunk_id": chunk.get("chunk_id"),
                "original_text": raw_text,
                "compressed_text": compressed_text,
                "relevance_score": score,
                "token_reduction_ratio": max(0.0, reduction_ratio)
            })

        return compressed_results