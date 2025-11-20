"""
Cache Manager for AYITI AI
Implements response caching for improved performance
"""

import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheManager:
    """
    LRU Cache for storing frequent query responses
    Features:
    - TTL (Time To Live) for cache entries
    - LRU eviction policy
    - Size limits
    - Cache hit/miss statistics
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 3600
    ):
        """
        Initialize cache manager

        Args:
            max_size: Maximum number of cache entries
            default_ttl_seconds: Default TTL in seconds (1 hour default)
        """
        self.max_size = max_size
        self.default_ttl = timedelta(seconds=default_ttl_seconds)
        self.cache = OrderedDict()
        self.metadata = {}

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _generate_key(
        self,
        query: str,
        language: str,
        sectors: list
    ) -> str:
        """
        Generate cache key from query parameters

        Args:
            query: Query text
            language: Language code
            sectors: List of sectors

        Returns:
            Cache key string
        """
        # Normalize inputs
        normalized_query = query.lower().strip()
        sorted_sectors = sorted(sectors)

        # Create key string
        key_data = {
            "query": normalized_query,
            "language": language,
            "sectors": sorted_sectors
        }

        key_string = json.dumps(key_data, sort_keys=True)

        # Hash for consistent key length
        key_hash = hashlib.md5(key_string.encode()).hexdigest()

        return key_hash

    def get(
        self,
        query: str,
        language: str,
        sectors: list
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available and not expired

        Args:
            query: Query text
            language: Language code
            sectors: List of sectors

        Returns:
            Cached response or None
        """
        key = self._generate_key(query, language, sectors)

        if key not in self.cache:
            self.misses += 1
            logger.debug(f"Cache miss for key: {key[:8]}...")
            return None

        # Check if expired
        meta = self.metadata.get(key)
        if meta and datetime.now() > meta["expires_at"]:
            # Expired, remove
            self._remove(key)
            self.misses += 1
            logger.debug(f"Cache expired for key: {key[:8]}...")
            return None

        # Cache hit - move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1

        logger.info(f"Cache hit for key: {key[:8]}... (hit rate: {self.get_hit_rate():.2%})")

        return self.cache[key]

    def set(
        self,
        query: str,
        language: str,
        sectors: list,
        response: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Store response in cache

        Args:
            query: Query text
            language: Language code
            sectors: List of sectors
            response: Response to cache
            ttl_seconds: Optional custom TTL
        """
        key = self._generate_key(query, language, sectors)

        # Check size limit
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Evict oldest (first in OrderedDict)
            oldest_key = next(iter(self.cache))
            self._remove(oldest_key)
            self.evictions += 1
            logger.debug(f"Evicted cache entry: {oldest_key[:8]}...")

        # Set TTL
        ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else self.default_ttl
        expires_at = datetime.now() + ttl

        # Store
        self.cache[key] = response
        self.metadata[key] = {
            "created_at": datetime.now(),
            "expires_at": expires_at,
            "query_preview": query[:50],
            "language": language,
            "sectors": sectors
        }

        # Move to end (most recently used)
        self.cache.move_to_end(key)

        logger.debug(f"Cached response for key: {key[:8]}... (TTL: {ttl.total_seconds()}s)")

    def _remove(self, key: str) -> None:
        """Remove entry from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.metadata:
            del self.metadata[key]

    def clear(self) -> None:
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        self.metadata.clear()
        logger.info(f"Cleared {count} cache entries")

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries

        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = []

        for key, meta in self.metadata.items():
            if now > meta["expires_at"]:
                expired_keys.append(key)

        for key in expired_keys:
            self._remove(key)

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "utilization": len(self.cache) / self.max_size if self.max_size > 0 else 0
        }

    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0

    def get_entries(self, limit: int = 10) -> list:
        """
        Get recent cache entries for debugging

        Args:
            limit: Number of entries to return

        Returns:
            List of cache entry info
        """
        entries = []

        for key in list(self.cache.keys())[-limit:]:
            meta = self.metadata.get(key, {})
            entries.append({
                "key": key[:16] + "...",
                "query_preview": meta.get("query_preview", ""),
                "language": meta.get("language", ""),
                "sectors": meta.get("sectors", []),
                "created_at": meta.get("created_at", "").isoformat() if meta.get("created_at") else "",
                "expires_at": meta.get("expires_at", "").isoformat() if meta.get("expires_at") else ""
            })

        return entries


# Global instance
cache_manager = CacheManager()
