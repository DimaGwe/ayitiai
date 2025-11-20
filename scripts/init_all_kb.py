#!/usr/bin/env python3
"""
Initialize All Knowledge Bases for AYITI AI
Load all sector knowledge bases into vector store
"""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_system.vector_store import vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


SECTORS = {
    "agriculture": "agriculture_kb.json",
    "education": "education_kb.json",
    "fishing": "fishing_kb.json",
    "infrastructure": "infrastructure_kb.json",
    "health": "health_kb.json"
}


def load_knowledge_base(sector: str, filename: str) -> bool:
    """
    Load a single knowledge base into vector store

    Args:
        sector: Sector name
        filename: Knowledge base JSON filename

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Loading {sector.upper()} Knowledge Base")
    logger.info(f"{'='*60}")

    # Load knowledge base JSON
    kb_path = Path(__file__).parent.parent / "knowledge_base" / sector / filename

    if not kb_path.exists():
        logger.error(f"Knowledge base file not found: {kb_path}")
        return False

    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file: {str(e)}")
        return False

    # Prepare documents for vector store
    documents = []
    metadatas = []

    # Process each category
    for category, items in kb_data.items():
        logger.info(f"  Processing category: {category}")

        for item in items:
            if isinstance(item, dict):
                # Multi-language entry
                for lang, text in item.items():
                    if lang in ['ht', 'en', 'fr', 'es']:
                        documents.append(text)
                        metadatas.append({
                            "sector": sector,
                            "category": category,
                            "language": lang,
                            "type": "knowledge_item"
                        })
            elif isinstance(item, str):
                # Single language entry
                documents.append(item)
                metadatas.append({
                    "sector": sector,
                    "category": category,
                    "language": "ht",  # Default to Kreyòl
                    "type": "knowledge_item"
                })

    logger.info(f"  Prepared {len(documents)} documents for indexing")

    # Add to vector store
    try:
        collection_name = f"{sector}_knowledge"

        # Delete existing collection if it exists
        existing_collections = vector_store.list_collections()
        if collection_name in existing_collections:
            logger.info(f"  Deleting existing collection: {collection_name}")
            vector_store.delete_collection(collection_name)

        # Add documents
        vector_store.add_documents(
            collection_name=collection_name,
            documents=documents,
            metadatas=metadatas
        )

        # Verify
        count = vector_store.get_collection_count(collection_name)
        logger.info(f"  ✓ Successfully loaded {count} documents into {collection_name}")

        return True

    except Exception as e:
        logger.error(f"  ✗ Error loading knowledge base: {str(e)}")
        return False


def main():
    """Load all knowledge bases"""

    logger.info("\n" + "="*60)
    logger.info("AYITI AI - Knowledge Base Initialization")
    logger.info("="*60 + "\n")

    results = {}

    # Load each sector
    for sector, filename in SECTORS.items():
        success = load_knowledge_base(sector, filename)
        results[sector] = success

    # Summary
    logger.info("\n" + "="*60)
    logger.info("INITIALIZATION SUMMARY")
    logger.info("="*60)

    successful = []
    failed = []

    for sector, success in results.items():
        if success:
            successful.append(sector)
            count = vector_store.get_collection_count(f"{sector}_knowledge")
            logger.info(f"✓ {sector.upper()}: {count} documents loaded")
        else:
            failed.append(sector)
            logger.error(f"✗ {sector.upper()}: FAILED")

    logger.info(f"\nTotal: {len(successful)}/{len(SECTORS)} sectors loaded successfully")

    if failed:
        logger.error(f"Failed sectors: {', '.join(failed)}")
        return False

    # List all collections
    logger.info("\n" + "="*60)
    logger.info("Available Collections:")
    logger.info("="*60)

    collections = vector_store.list_collections()
    for collection in collections:
        count = vector_store.get_collection_count(collection)
        logger.info(f"  - {collection}: {count} documents")

    logger.info("\n" + "="*60)
    logger.info("Knowledge Base Initialization Complete!")
    logger.info("="*60 + "\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
