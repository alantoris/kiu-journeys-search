"""
Cache Service - Redis-based caching for flight events
"""
import json
import logging
from typing import Optional, List
from datetime import date
import aioredis
from django.conf import settings

from ...core.entities.flight_event import FlightEvent

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based cache service for storing and retrieving flight events.
    
    This service provides caching functionality to avoid repeated API calls
    for the same flight data. Flight events are cached by date with a configurable TTL.
    """
    
    def __init__(self, redis_url: str = None, ttl: int = None):
        """
        Initialize the cache service.
        
        Args:
            redis_url: Redis connection URL (defaults to settings.REDIS_URL)
            ttl: Time to live in seconds (defaults to settings.CACHE_TTL)
        """
        self.redis_url = redis_url or getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        self.ttl = ttl or getattr(settings, 'CACHE_TTL', 3600)
        self._redis: Optional[aioredis.Redis] = None
    
    async def _get_redis(self) -> aioredis.Redis:
        """
        Get Redis connection (lazy initialization).
        
        Returns:
            Redis connection instance
        """
        if self._redis is None:
            self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        return self._redis
    
    def _get_cache_key(self, search_date: date) -> str:
        """
        Generate cache key for flight events on a specific date.
        
        Args:
            search_date: Date to search for
            
        Returns:
            Cache key string
        """
        return f"flight_events:{search_date.isoformat()}"
    
    async def get_flight_events(self, search_date: date) -> Optional[List[FlightEvent]]:
        """
        Get flight events from cache for a specific date.
        
        Args:
            search_date: Date to search for
            
        Returns:
            List of flight events if found in cache, None otherwise
        """
        try:
            redis = await self._get_redis()
            cache_key = self._get_cache_key(search_date)
            
            cached_data = await redis.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for flight events on {search_date}")
                flight_data = json.loads(cached_data)
                return [FlightEvent(**event) for event in flight_data]
            else:
                logger.info(f"Cache miss for flight events on {search_date}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    async def set_flight_events(self, search_date: date, flight_events: List[FlightEvent]) -> bool:
        """
        Store flight events in cache for a specific date.
        
        Args:
            search_date: Date the events belong to
            flight_events: List of flight events to cache
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            redis = await self._get_redis()
            cache_key = self._get_cache_key(search_date)
            
            # Convert FlightEvent objects to dictionaries for JSON serialization
            flight_data = [
                {
                    'flight_number': event.flight_number,
                    'from_city': event.from_city,
                    'to_city': event.to_city,
                    'departure_time': event.departure_time.isoformat(),
                    'arrival_time': event.arrival_time.isoformat()
                }
                for event in flight_events
            ]
            
            await redis.setex(
                cache_key, 
                self.ttl, 
                json.dumps(flight_data)
            )
            
            logger.info(f"Cached {len(flight_events)} flight events for {search_date}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing in cache: {str(e)}")
            return False
    
    async def delete_flight_events(self, search_date: date) -> bool:
        """
        Delete flight events from cache for a specific date.
        
        Args:
            search_date: Date to delete from cache
            
        Returns:
            True if successfully deleted, False otherwise
        """
        try:
            redis = await self._get_redis()
            cache_key = self._get_cache_key(search_date)
            
            deleted_count = await redis.delete(cache_key)
            if deleted_count > 0:
                logger.info(f"Deleted flight events from cache for {search_date}")
                return True
            else:
                logger.info(f"No flight events found in cache for {search_date}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
    
    async def clear_all_cache(self) -> bool:
        """
        Clear all flight events cache.
        
        Returns:
            True if successfully cleared, False otherwise
        """
        try:
            redis = await self._get_redis()
            
            # Delete all keys matching the flight_events pattern
            keys = await redis.keys("flight_events:*")
            if keys:
                deleted_count = await redis.delete(*keys)
                logger.info(f"Cleared {deleted_count} flight event cache entries")
                return True
            else:
                logger.info("No flight event cache entries found to clear")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    async def close(self):
        """
        Close Redis connection.
        """
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")
