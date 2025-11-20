"""
API Endpoints for AYITI AI
Query processing and knowledge base management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging
from datetime import datetime

from core.llm_integration import llm
from core.multilingual_handler import multilingual
from core.context_router import router
from core.conversation_memory import conversation_memory
from core.cache_manager import cache_manager
from core.performance_monitor import performance_monitor
from rag_system.retrieval_engine import retrieval_engine

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# Request/Response Models
class QueryRequest(BaseModel):
    """Query request model"""
    message: str = Field(..., description="User query message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    language_preference: Optional[str] = Field(None, description="Preferred language code (ht, fr, en, es)")
    explicit_sectors: Optional[List[str]] = Field(None, description="Optional explicit sector list")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Kijan mwen ka amelyore pwodiksyon agrik�l mwen?",
                "language_preference": "ht",
                "explicit_sectors": ["agriculture"]
            }
        }


class QueryResponse(BaseModel):
    """Query response model"""
    response: str = Field(..., description="AI-generated response")
    conversation_id: str = Field(..., description="Conversation ID for follow-up queries")
    sectors_used: List[str] = Field(..., description="Sectors used for response")
    primary_sector: str = Field(..., description="Primary sector detected")
    sources_consulted: List[str] = Field(..., description="Knowledge sources consulted")
    confidence_score: float = Field(..., description="Response confidence score")
    language: str = Field(..., description="Response language")
    cost: float = Field(..., description="Request cost in USD")
    timestamp: str = Field(..., description="Response timestamp")


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process user query and return AI-generated response

    Args:
        request: Query request with message and optional parameters

    Returns:
        QueryResponse with answer and metadata
    """
    try:
        start_time = datetime.now()

        # Handle conversation ID
        conv_id = request.conversation_id
        if not conv_id:
            conv_id = conversation_memory.create_conversation_id()

        # Get conversation history
        conversation_history = conversation_memory.get_recent_messages(conv_id, n=5)

        # Detect language
        if request.language_preference:
            detected_language = request.language_preference
            language_confidence = 1.0
        else:
            detected_language, language_confidence = multilingual.detect_language(
                request.message
            )

        logger.info(
            f"Processing query in {detected_language} "
            f"(confidence: {language_confidence:.2f}, conv_id: {conv_id})"
        )

        # Detect sectors (considering conversation history)
        if request.explicit_sectors:
            sectors = [(sector, 1.0) for sector in request.explicit_sectors]
        else:
            sectors = router.analyze_query_intent(request.message, conversation_history)

        primary_sector = router.get_primary_sector(sectors) or "general"

        # Check cache (only for non-conversation queries to avoid stale context)
        cached_response = None
        if not conversation_history:
            sector_names = [s for s, _ in sectors]
            cached_response = cache_manager.get(
                query=request.message,
                language=detected_language,
                sectors=sector_names
            )

        if cached_response:
            logger.info("Returning cached response")
            # Add to conversation memory
            conversation_memory.add_message(
                conversation_id=conv_id,
                role="user",
                content=request.message,
                metadata={
                    "language": detected_language,
                    "sectors": [s for s, _ in sectors],
                    "primary_sector": primary_sector,
                    "cached": True
                }
            )
            conversation_memory.add_message(
                conversation_id=conv_id,
                role="assistant",
                content=cached_response['response'],
                metadata={
                    "cost": 0.0,
                    "cached": True
                }
            )

            return QueryResponse(
                response=cached_response['response'],
                conversation_id=conv_id,
                sectors_used=cached_response['sectors_used'],
                primary_sector=cached_response['primary_sector'],
                sources_consulted=cached_response['sources_consulted'],
                confidence_score=cached_response['confidence_score'],
                language=detected_language,
                cost=0.0,  # No cost for cached responses
                timestamp=datetime.now().isoformat()
            )

        # Retrieve relevant knowledge
        rag_results = retrieval_engine.search_and_format(
            query=request.message,
            sectors=sectors,
            language=detected_language
        )

        # Generate cultural context
        cultural_context = multilingual.generate_cultural_context(
            detected_language,
            primary_sector
        )

        # Build messages for LLM with conversation context
        system_context = f"""Context from knowledge base:
{rag_results['context']}

Cultural considerations:
{cultural_context}

Please provide a helpful, practical response based on this context."""

        messages = conversation_history + [
            {"role": "user", "content": request.message}
        ]

        # Add system context
        if messages:
            messages.insert(0, {"role": "system", "content": system_context})

        # Generate response
        llm_response = await llm.generate_response(
            messages=messages,
            sector_context=primary_sector,
            language=detected_language
        )

        # Check for errors
        if "error" in llm_response:
            raise HTTPException(
                status_code=500,
                detail=f"LLM error: {llm_response['error']}"
            )

        # Store in conversation memory
        conversation_memory.add_message(
            conversation_id=conv_id,
            role="user",
            content=request.message,
            metadata={
                "language": detected_language,
                "sectors": [s for s, _ in sectors],
                "primary_sector": primary_sector
            }
        )

        conversation_memory.add_message(
            conversation_id=conv_id,
            role="assistant",
            content=llm_response['response'],
            metadata={
                "cost": llm_response['cost'],
                "sectors_used": rag_results['sectors_used']
            }
        )

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()

        # Record performance metrics
        performance_monitor.record_request(
            latency=processing_time,
            cost=llm_response['cost'],
            sector=primary_sector,
            language=detected_language,
            success=True
        )

        logger.info(
            f"Query processed in {processing_time:.2f}s, "
            f"cost: ${llm_response['cost']:.4f}"
        )

        # Cache response (only for non-conversation queries)
        if not conversation_history:
            sector_names = [s for s, _ in sectors]
            cache_data = {
                "response": llm_response['response'],
                "sectors_used": rag_results['sectors_used'],
                "primary_sector": primary_sector,
                "sources_consulted": [s['sector'] for s in rag_results['sources']],
                "confidence_score": sectors[0][1] if sectors else 0.5
            }
            cache_manager.set(
                query=request.message,
                language=detected_language,
                sectors=sector_names,
                response=cache_data,
                ttl_seconds=3600  # 1 hour TTL
            )

        # Build response
        return QueryResponse(
            response=llm_response['response'],
            conversation_id=conv_id,
            sectors_used=rag_results['sectors_used'],
            primary_sector=primary_sector,
            sources_consulted=[s['sector'] for s in rag_results['sources']],
            confidence_score=sectors[0][1] if sectors else 0.5,
            language=detected_language,
            cost=llm_response['cost'],
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/stats/cost")
async def get_cost_stats():
    """
    Get current cost statistics

    Returns:
        Cost statistics including daily total and breakdown
    """
    try:
        stats = llm.get_cost_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting cost stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting cost stats: {str(e)}"
        )


@router.get("/stats/knowledge")
async def get_knowledge_stats():
    """
    Get knowledge base statistics

    Returns:
        Statistics about available knowledge bases
    """
    try:
        stats = retrieval_engine.get_sector_stats()
        return {
            "sectors": stats,
            "total_collections": len(stats)
        }

    except Exception as e:
        logger.error(f"Error getting knowledge stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting knowledge stats: {str(e)}"
        )


@router.get("/sectors")
async def list_sectors():
    """
    List all available sectors

    Returns:
        List of available sectors with descriptions
    """
    sectors = {
        "agriculture": {
            "name": "Agriculture",
            "description": "Farming, crops, livestock, and sustainable practices",
            "keywords_example": ["jaden", "plante", "rek�t", "farming", "crops"]
        },
        "education": {
            "name": "Education",
            "description": "Schools, learning, curriculum, and teaching methods",
            "keywords_example": ["lek�l", "aprann", "edikasyon", "school", "learning"]
        },
        "fishing": {
            "name": "Fishing",
            "description": "Fishing, aquaculture, and marine resources",
            "keywords_example": ["lap�ch", "pwason", "lanm�", "fishing", "fish"]
        },
        "infrastructure": {
            "name": "Infrastructure",
            "description": "Buildings, roads, water, energy, and sanitation",
            "keywords_example": ["konstriksyon", "wout", "dlo", "construction", "roads"]
        },
        "health": {
            "name": "Health",
            "description": "Healthcare, medicine, prevention, and wellness",
            "keywords_example": ["sante", "malad", "dokt�", "health", "medicine"]
        },
        "governance": {
            "name": "Governance",
            "description": "Government, laws, regulations, and civic participation",
            "keywords_example": ["gouv�nman", "lwa", "dwa", "government", "law"]
        }
    }

    return sectors


@router.get("/languages")
async def list_languages():
    """
    List supported languages

    Returns:
        List of supported language codes and names
    """
    return {
        "supported": [
            {"code": "ht", "name": "Haitian Creole (Krey�l)", "priority": "primary"},
            {"code": "fr", "name": "French (Fran�ais)", "priority": "secondary"},
            {"code": "en", "name": "English", "priority": "secondary"},
            {"code": "es", "name": "Spanish (Espa�ol)", "priority": "secondary"}
        ],
        "default": "ht"
    }


@router.post("/admin/knowledge/reload")
async def reload_knowledge_base(sector: str):
    """
    Reload knowledge base for a specific sector

    Args:
        sector: Sector name to reload

    Returns:
        Success message
    """
    # This would be implemented based on specific reload logic
    # For now, just a placeholder
    return {
        "status": "success",
        "message": f"Knowledge base reload for {sector} would be triggered here",
        "sector": sector
    }


@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history

    Args:
        conversation_id: Conversation ID

    Returns:
        Conversation history and statistics
    """
    try:
        history = conversation_memory.get_conversation_history(
            conversation_id,
            include_metadata=True
        )

        stats = conversation_memory.get_conversation_stats(conversation_id)

        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found"
            )

        return {
            "conversation_id": conversation_id,
            "history": history,
            "stats": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting conversation: {str(e)}"
        )


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete conversation history

    Args:
        conversation_id: Conversation ID

    Returns:
        Success message
    """
    try:
        conversation_memory.clear_conversation(conversation_id)

        return {
            "status": "success",
            "message": f"Conversation {conversation_id} deleted",
            "conversation_id": conversation_id
        }

    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting conversation: {str(e)}"
        )


@router.get("/stats/conversations")
async def get_conversation_stats():
    """
    Get statistics about all conversations

    Returns:
        Overall conversation statistics
    """
    try:
        stats = conversation_memory.get_all_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting conversation stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting conversation stats: {str(e)}"
        )


@router.get("/stats/cache")
async def get_cache_stats():
    """
    Get cache statistics

    Returns:
        Cache performance statistics
    """
    try:
        stats = cache_manager.get_stats()
        return stats

    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting cache stats: {str(e)}"
        )


@router.post("/admin/cache/clear")
async def clear_cache():
    """
    Clear all cache entries

    Returns:
        Success message with count of cleared entries
    """
    try:
        count_before = cache_manager.get_stats()["size"]
        cache_manager.clear()

        return {
            "status": "success",
            "message": f"Cache cleared",
            "entries_cleared": count_before
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing cache: {str(e)}"
        )


@router.post("/admin/cache/cleanup")
async def cleanup_cache():
    """
    Remove expired cache entries

    Returns:
        Number of entries removed
    """
    try:
        removed = cache_manager.cleanup_expired()

        return {
            "status": "success",
            "message": f"Cleaned up expired cache entries",
            "entries_removed": removed
        }

    except Exception as e:
        logger.error(f"Error cleaning cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cleaning cache: {str(e)}"
        )


@router.get("/stats/performance")
async def get_performance_stats():
    """
    Get performance statistics

    Returns:
        Comprehensive performance metrics
    """
    try:
        metrics = performance_monitor.get_full_report()
        return metrics

    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting performance stats: {str(e)}"
        )


@router.get("/stats/overview")
async def get_system_overview():
    """
    Get comprehensive system overview

    Returns:
        Complete system statistics including cost, cache, conversations, and performance
    """
    try:
        return {
            "cost": llm.get_cost_stats(),
            "cache": cache_manager.get_stats(),
            "conversations": conversation_memory.get_all_stats(),
            "performance": performance_monitor.get_metrics(),
            "knowledge_base": retrieval_engine.get_sector_stats()
        }

    except Exception as e:
        logger.error(f"Error getting system overview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting system overview: {str(e)}"
        )
