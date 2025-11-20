#!/usr/bin/env python3
"""
Initialize Agriculture Knowledge Base
Load agriculture knowledge into vector store
"""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_system.vector_store import vector_store
from rag_system.document_processor import doc_processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_agriculture_knowledge():
    """Load agriculture knowledge base into vector store"""

    logger.info("Starting agriculture knowledge base initialization...")

    # Load knowledge base JSON
    kb_path = Path(__file__).parent.parent / "knowledge_base" / "agriculture" / "agriculture_kb.json"

    if not kb_path.exists():
        logger.error(f"Knowledge base file not found: {kb_path}")
        return False

    with open(kb_path, 'r', encoding='utf-8') as f:
        agriculture_kb = json.load(f)

    # Prepare documents for vector store
    documents = []
    metadatas = []

    # Process each category
    for category, items in agriculture_kb.items():
        logger.info(f"Processing category: {category}")

        for item in items:
            if isinstance(item, dict):
                # Multi-language entry
                for lang, text in item.items():
                    if lang in ['ht', 'en', 'fr', 'es']:
                        documents.append(text)
                        metadatas.append({
                            "sector": "agriculture",
                            "category": category,
                            "language": lang,
                            "type": "knowledge_item"
                        })
            elif isinstance(item, str):
                # Single language entry
                documents.append(item)
                metadatas.append({
                    "sector": "agriculture",
                    "category": category,
                    "language": "ht",  # Default to Kreyòl
                    "type": "knowledge_item"
                })

    logger.info(f"Prepared {len(documents)} documents for indexing")

    # Add to vector store
    try:
        vector_store.add_documents(
            collection_name="agriculture_knowledge",
            documents=documents,
            metadatas=metadatas
        )

        # Verify
        count = vector_store.get_collection_count("agriculture_knowledge")
        logger.info(f"Successfully loaded {count} documents into agriculture_knowledge collection")

        return True

    except Exception as e:
        logger.error(f"Error loading knowledge base: {str(e)}")
        return False


if __name__ == "__main__":
    success = load_agriculture_knowledge()

    if success:
        logger.info("Agriculture knowledge base initialization completed successfully!")
        sys.exit(0)
    else:
        logger.error("Agriculture knowledge base initialization failed!")
        sys.exit(1)
