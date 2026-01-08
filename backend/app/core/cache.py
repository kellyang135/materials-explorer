"""Simple in-memory cache for local development."""

import json
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

from app.core.config import settings


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if key in self._cache:
                entry = self._cache[key]
                # Check if expired
                if entry["expires"] > datetime.now():
                    return entry["value"]
                else:
                    # Remove expired entry
                    del self._cache[key]
        except Exception:
            # Cache error, skip
            pass
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache with optional TTL."""
        try:
            ttl = ttl or settings.CACHE_TTL_SECONDS
            expires = datetime.now() + timedelta(seconds=ttl)
            self._cache[key] = {
                "value": value,
                "expires": expires
            }
            
            # Simple cleanup: remove expired entries occasionally
            if len(self._cache) % 100 == 0:  # Every 100 additions
                self._cleanup_expired()
                
        except Exception:
            # Cache error, skip
            pass

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        try:
            if key in self._cache:
                del self._cache[key]
        except Exception:
            pass

    async def clear_pattern(self, pattern: str) -> None:
        """Clear all keys matching pattern (simple implementation)."""
        try:
            # Simple pattern matching for basic wildcards
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                keys_to_delete = [key for key in self._cache.keys() if key.startswith(prefix)]
                for key in keys_to_delete:
                    del self._cache[key]
        except Exception:
            pass

    async def close(self) -> None:
        """Close cache (no-op for in-memory)."""
        pass
        
    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items() 
            if entry["expires"] <= now
        ]
        for key in expired_keys:
            del self._cache[key]


# Global cache instance
cache = SimpleCache()
