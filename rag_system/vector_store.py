"""
Vector Store for AYITI AI RAG System
Manages embedding storage and retrieval using ChromaDB
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import logging
from pathlib import Path
import uuid

from core.config_manager import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector database for storing and retrieving document embeddings
    Uses ChromaDB for efficient similarity search
    """

    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize vector store

        Args:
            persist_directory: Directory to persist vector DB
        """
        self.persist_directory = persist_directory or settings.vector_db_path

        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False
            )
        )

        # Collection cache
        self.collections = {}

        logger.info(f"Vector store initialized at {self.persist_directory}")

    def get_or_create_collection(
        self,
        collection_name: str,
        metadata: Optional[Dict] = None
    ) -> chromadb.Collection:
        """
        Get existing collection or create new one

        Args:
            collection_name: Name of the collection
            metadata: Optional metadata for collection

        Returns:
            ChromaDB collection
        """
        if collection_name in self.collections:
            return self.collections[collection_name]

        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata=metadata or {}
            )

            self.collections[collection_name] = collection
            logger.info(f"Collection '{collection_name}' ready")

            return collection

        except Exception as e:
            logger.error(f"Error getting/creating collection: {str(e)}")
            raise

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to a collection

        Args:
            collection_name: Target collection
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for documents (auto-generated if not provided)
        """
        collection = self.get_or_create_collection(collection_name)

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        # Ensure metadatas match document count
        if metadatas is None:
            metadatas = [{} for _ in documents]

        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            logger.info(
                f"Added {len(documents)} documents to collection '{collection_name}'"
            )

        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise

    def query(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query collection for similar documents

        Args:
            collection_name: Collection to query
            query_texts: Query text(s)
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Query results with documents, distances, and metadata
        """
        collection = self.get_or_create_collection(collection_name)

        try:
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where
            )

            logger.info(
                f"Query returned {len(results['documents'][0])} results "
                f"from '{collection_name}'"
            )

            return results

        except Exception as e:
            logger.error(f"Error querying collection: {str(e)}")
            return {
                "documents": [[]],
                "distances": [[]],
                "metadatas": [[]]
            }

    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection

        Args:
            collection_name: Collection to delete
        """
        try:
            self.client.delete_collection(name=collection_name)

            if collection_name in self.collections:
                del self.collections[collection_name]

            logger.info(f"Deleted collection '{collection_name}'")

        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise

    def list_collections(self) -> List[str]:
        """
        List all collections in the vector store

        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]

        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []

    def get_collection_count(self, collection_name: str) -> int:
        """
        Get number of documents in a collection

        Args:
            collection_name: Collection name

        Returns:
            Number of documents
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            return collection.count()

        except Exception as e:
            logger.error(f"Error getting collection count: {str(e)}")
            return 0

    def update_document(
        self,
        collection_name: str,
        doc_id: str,
        document: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Update a document in the collection

        Args:
            collection_name: Collection name
            doc_id: Document ID
            document: New document text
            metadata: Optional new metadata
        """
        collection = self.get_or_create_collection(collection_name)

        try:
            collection.update(
                ids=[doc_id],
                documents=[document],
                metadatas=[metadata] if metadata else None
            )

            logger.info(f"Updated document {doc_id} in '{collection_name}'")

        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise


# Global instance
vector_store = VectorStore()
