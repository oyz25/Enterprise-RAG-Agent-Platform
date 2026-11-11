import re
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi


class BM25SearchService:
    """
    In-memory BM25 Okapi sparse search engine for exact keyword matching.
    """

    def __init__(self):
        self.corpus_chunks: List[Dict[str, Any]] = []
        self.bm25_index: BM25Okapi = None

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        Tokenize input text into lowercase alphanumeric tokens.
        """
        clean_text = re.sub(r"[^\w\s]", "", text.lower())
        return clean_text.split()

    def build_index(self, chunks: List[Dict[str, Any]]):
        """
        Build BM25 index from document chunks payload.
        """
        if not chunks:
            self.corpus_chunks = []
            self.bm25_index = None
            return

        self.corpus_chunks = chunks
        tokenized_corpus = [self._tokenize(chunk["text"]) for chunk in chunks]
        self.bm25_index = BM25Okapi(tokenized_corpus)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Execute BM25 keyword search against indexed corpus and return ranked results.
        """
        if not self.bm25_index or not self.corpus_chunks:
            return []

        tokenized_query = self._tokenize(query)
        scores = self.bm25_index.get_scores(tokenized_query)

        # Pair score with chunk and sort in descending order
        scored_chunks = []
        for idx, score in enumerate(scores):
            if score > 0.0:  # Exclude zero-relevance matches
                chunk = self.corpus_chunks[idx].copy()
                chunk["bm25_score"] = round(float(score), 4)
                scored_chunks.append(chunk)

        scored_chunks.sort(key=lambda x: x["bm25_score"], reverse=True)
        return scored_chunks[:top_k]