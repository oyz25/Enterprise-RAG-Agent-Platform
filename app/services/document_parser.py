import io
from typing import Dict, Any, Tuple
from pypdf import PdfReader


class DocumentParser:
    """
    Utility service to parse various document formats into raw text and extracted metadata.
    """

    @staticmethod
    def parse_txt(file_content: bytes) -> str:
        """
        Extract text from plain text files.
        """
        return file_content.decode("utf-8", errors="ignore")

    @staticmethod
    def parse_markdown(file_content: bytes) -> str:
        """
        Extract text from Markdown files.
        """
        return file_content.decode("utf-8", errors="ignore")

    @staticmethod
    def parse_pdf(file_content: bytes) -> Tuple[str, int]:
        """
        Extract text from PDF files and return extracted text along with the total page count.
        """
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        num_pages = len(reader.pages)
        
        extracted_pages = []
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            extracted_pages.append(f"--- Page {idx + 1} ---\n{text}")
            
        return "\n\n".join(extracted_pages), num_pages

    @classmethod
    def extract(cls, filename: str, file_content: bytes) -> Tuple[str, Dict[str, Any]]:
        """
        Main entry point to dispatch parsing based on file extension.
        """
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        metadata = {
            "filename": filename,
            "file_type": ext,
            "file_size_bytes": len(file_content)
        }

        if ext == "pdf":
            text, pages = cls.parse_pdf(file_content)
            metadata["total_pages"] = pages
        elif ext in ["txt", "text"]:
            text = cls.parse_txt(file_content)
            metadata["total_pages"] = 1
        elif ext in ["md", "markdown"]:
            text = cls.parse_markdown(file_content)
            metadata["total_pages"] = 1
        else:
            raise ValueError(f"Unsupported file format: .{ext}")

        return text, metadata