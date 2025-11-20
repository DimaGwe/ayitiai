"""
Retrieval Engine for AYITI AI RAG System
Coordinates vector search and context formatting
"""

from typing import List, Dict, Optional, Tuple
import logging

from rag_system.vector_store import vector_store
from core.context_router import router

logger = logging.getLogger(__name__)


class KnowledgeRetrieval:
    """
    Unified retrieval across all sector knowledge bases
    """

    def __init__(self, default_n_results: int = 5):
        """
        Initialize retrieval engine

        Args:
            default_n_results: Default number of results to retrieve
        """
        self.vector_store = vector_store
        self.router = router
        self.default_n_results = default_n_results

    def retrieve_sector_knowledge(
        self,
        query: str,
        sectors: List[Tuple[str, float]],
        language: str = "ht",
        n_results: int = None
    ) -> List[Dict]:
        """
        Search across multiple vector stores and rank results

        Args:
            query: Search query
            sectors: List of (sector, confidence) tuples
            language: Query language
            n_results: Number of results per sector

        Returns:
            List of relevant documents with metadata
        """
        n_results = n_results or self.default_n_results
        all_results = []

        for sector, confidence in sectors:
            if confidence < 0.3:  # Skip low-confidence sectors
                continue

            collection_name = f"{sector}_knowledge"

            try:
                # Query vector store
                results = self.vector_store.query(
                    collection_name=collection_name,
                    query_texts=[query],
                    n_results=n_results
                )

                # Process results
                if results and results['documents'] and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                        distance = results['distances'][0][i] if results['distances'] else 1.0

                        all_results.append({
                            "content": doc,
                            "sector": sector,
                            "sector_confidence": confidence,
                            "relevance_score": 1.0 - distance,  # Convert distance to similarity
                            "metadata": metadata
                        })

            except Exception as e:
                logger.warning(
                    f"Could not retrieve from {collection_name}: {str(e)}"
                )
                continue

        # Sort by combined score (sector confidence * relevance)
        all_results.sort(
            key=lambda x: x['sector_confidence'] * x['relevance_score'],
            reverse=True
        )

        logger.info(f"Retrieved {len(all_results)} total results")
        return all_results[:n_results * 2]  # Return top results

    def format_context(
        self,
        retrieved_docs: List[Dict],
        primary_sector: str,
        max_context_length: int = 2000
    ) -> str:
        """
        Structure information for optimal LLM consumption

        Args:
            retrieved_docs: Retrieved documents
            primary_sector: Primary sector for query
            max_context_length: Maximum context length in characters

        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return "No specific knowledge found for this query."

        context_parts = []
        current_length = 0

        # Group by sector
        by_sector = {}
        for doc in retrieved_docs:
            sector = doc['sector']
            if sector not in by_sector:
                by_sector[sector] = []
            by_sector[sector].append(doc)

        # Format primary sector first
        if primary_sector in by_sector:
            context_parts.append(f"## {primary_sector.title()} Information\n")

            for doc in by_sector[primary_sector]:
                content = doc['content']
                if current_length + len(content) > max_context_length:
                    break

                context_parts.append(f"- {content}\n")
                current_length += len(content)

        # Add other relevant sectors
        for sector, docs in by_sector.items():
            if sector == primary_sector:
                continue

            if current_length >= max_context_length:
                break

            context_parts.append(f"\n## Related {sector.title()} Information\n")

            for doc in docs:
                content = doc['content']
                if current_length + len(content) > max_context_length:
                    break

                context_parts.append(f"- {content}\n")
                current_length += len(content)

        formatted = "".join(context_parts)
        logger.info(f"Formatted context: {len(formatted)} characters")

        return formatted

    def search_and_format(
        self,
        query: str,
        sectors: Optional[List[Tuple[str, float]]] = None,
        language: str = "ht",
        n_results: int = None
    ) -> Dict:
        """
        Complete search and format pipeline

        Args:
            query: Search query
            sectors: Optional pre-detected sectors
            language: Query language
            n_results: Number of results

        Returns:
            Dict with formatted context and metadata
        """
        # Detect sectors if not provided
        if sectors is None:
            sectors = self.router.analyze_query_intent(query)

        # Retrieve relevant documents
        docs = self.retrieve_sector_knowledge(
            query=query,
            sectors=sectors,
            language=language,
            n_results=n_results
        )

        # Get primary sector
        primary_sector = self.router.get_primary_sector(sectors) or "general"

        # Format context
        context = self.format_context(
            retrieved_docs=docs,
            primary_sector=primary_sector
        )

        return {
            "context": context,
            "sectors_used": [s for s, _ in sectors],
            "primary_sector": primary_sector,
            "documents_retrieved": len(docs),
            "sources": [
                {
                    "sector": doc['sector'],
                    "relevance": doc['relevance_score'],
                    "preview": doc['content'][:100] + "..."
                }
                for doc in docs[:5]  # Top 5 sources
            ]
        }

    def get_sector_stats(self) -> Dict:
        """
        Get statistics about available knowledge bases

        Returns:
            Dict with sector statistics
        """
        collections = self.vector_store.list_collections()
        stats = {}

        for collection in collections:
            if collection.endswith('_knowledge'):
                sector = collection.replace('_knowledge', '')
                count = self.vector_store.get_collection_count(collection)
                stats[sector] = {
                    "document_count": count,
                    "collection": collection
                }

        return stats


# Global instance
retrieval_engine = KnowledgeRetrieval()
