"""
Document Processor for AYITI AI RAG System
Handles document loading, chunking, and preprocessing
"""

from typing import List, Dict, Optional
import logging
from pathlib import Path
import json
import re

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Process documents for vector storage
    Handles text chunking, cleaning, and metadata extraction
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        Initialize document processor

        Args:
            chunk_size: Target size for text chunks (in characters)
            chunk_overlap: Overlap between chunks (in characters)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_text_file(self, file_path: str) -> str:
        """
        Load text from file

        Args:
            file_path: Path to text file

        Returns:
            File contents as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.info(f"Loaded {len(content)} characters from {file_path}")
            return content

        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            return ""

    def load_json_file(self, file_path: str) -> Dict:
        """
        Load JSON file

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"Loaded JSON from {file_path}")
            return data

        except Exception as e:
            logger.error(f"Error loading JSON {file_path}: {str(e)}")
            return {}

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-\'\"]', '', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to chunk
            chunk_size: Override default chunk size
            chunk_overlap: Override default overlap

        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                last_period = text.rfind('.', start, end)
                last_question = text.rfind('?', start, end)
                last_exclamation = text.rfind('!', start, end)

                sentence_end = max(last_period, last_question, last_exclamation)

                if sentence_end > start:
                    end = sentence_end + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - chunk_overlap

        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks

    def process_document(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Process a document into chunks with metadata

        Args:
            content: Document content
            metadata: Optional metadata to attach

        Returns:
            List of chunk dicts with text and metadata
        """
        # Clean text
        cleaned = self.clean_text(content)

        # Chunk text
        chunks = self.chunk_text(cleaned)

        # Create chunk objects
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "text": chunk,
                "metadata": {
                    **(metadata or {}),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_length": len(chunk)
                }
            }
            processed_chunks.append(chunk_data)

        logger.info(f"Processed document into {len(processed_chunks)} chunks")
        return processed_chunks

    def process_knowledge_base(
        self,
        knowledge_data: Dict,
        sector: str
    ) -> List[Dict]:
        """
        Process knowledge base data into chunks

        Args:
            knowledge_data: Structured knowledge data
            sector: Sector name

        Returns:
            List of processed chunks
        """
        all_chunks = []

        for category, items in knowledge_data.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        chunks = self.process_document(
                            content=item,
                            metadata={
                                "sector": sector,
                                "category": category,
                                "type": "knowledge_item"
                            }
                        )
                        all_chunks.extend(chunks)

        logger.info(
            f"Processed {len(all_chunks)} chunks from {sector} knowledge base"
        )
        return all_chunks

    def batch_process_directory(
        self,
        directory: str,
        sector: str,
        file_pattern: str = "*.txt"
    ) -> List[Dict]:
        """
        Process all files in a directory

        Args:
            directory: Directory path
            sector: Sector name
            file_pattern: File pattern to match

        Returns:
            List of processed chunks
        """
        dir_path = Path(directory)
        all_chunks = []

        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return all_chunks

        for file_path in dir_path.glob(file_pattern):
            content = self.load_text_file(str(file_path))

            if content:
                chunks = self.process_document(
                    content=content,
                    metadata={
                        "sector": sector,
                        "source_file": file_path.name,
                        "file_path": str(file_path)
                    }
                )
                all_chunks.extend(chunks)

        logger.info(
            f"Processed {len(all_chunks)} chunks from directory {directory}"
        )
        return all_chunks


# Global instance
doc_processor = DocumentProcessor()
