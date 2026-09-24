import uuid
import tiktoken
from typing import List, Dict, Any


class ChunkingEngine:
    """
    Service responsible for splitting raw document text into logical chunks.
    """

    @staticmethod
    def count_tokens(text: str, model_name: str = "gpt-3.5-turbo") -> int:
        """
        Calculate the exact number of tokens in a string using tiktoken.
        """
        try:
            encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    @classmethod
    def recursive_character_chunking(
        cls, 
        text: str, 
        metadata: Dict[str, Any], 
        chunk_size: int = 500, 
        chunk_overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Recursively split text by separators (paragraphs, lines, spaces) while preserving overlap.
        """
        separators = ["\n\n", "\n", " ", ""]
        
        def _split_text(input_text: str, current_separators: List[str]) -> List[str]:
            if not input_text:
                return []
            if len(input_text) <= chunk_size:
                return [input_text]
            
            sep = current_separators[0] if current_separators else ""
            next_separators = current_separators[1:] if len(current_separators) > 1 else []
            
            splits = input_text.split(sep) if sep else list(input_text)
            
            docs = []
            current_doc = []
            total_len = 0
            
            for split in splits:
                split_len = len(split)
                if total_len + split_len + (len(sep) if current_doc else 0) > chunk_size:
                    if current_doc:
                        doc_str = sep.join(current_doc)
                        if doc_str:
                            docs.append(doc_str)
                        while total_len > chunk_overlap and current_doc:
                            removed = current_doc.pop(0)
                            total_len -= (len(removed) + len(sep))
                    if split_len > chunk_size and next_separators:
                        docs.extend(_split_text(split, next_separators))
                        current_doc = []
                        total_len = 0
                    else:
                        current_doc = [split]
                        total_len = split_len
                else:
                    current_doc.append(split)
                    total_len += split_len + (len(sep) if len(current_doc) > 1 else 0)
            
            if current_doc:
                docs.append(sep.join(current_doc))
            return docs

        raw_chunks = _split_text(text, separators)
        
        chunks = []
        for idx, chunk_text in enumerate(raw_chunks):
            chunk_meta = metadata.copy()
            chunk_meta["chunk_index"] = idx
            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "text": chunk_text,
                "index": idx,
                "token_count": cls.count_tokens(chunk_text),
                "metadata": chunk_meta
            })
        
        return chunks