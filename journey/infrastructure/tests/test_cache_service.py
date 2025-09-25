"""
Tests for CacheService - Redis-based caching functionality
"""
import pytest
import json
from unittest.mock import AsyncMock, patch
from datetime import date, datetime

from ..adapters.cache_service import CacheService
from ...core.entities.flight_event import FlightEvent


class TestCacheService:
    """Tests for CacheService class."""

    @pytest.fixture
    def cache_service(self):
        """Create a CacheService instance for testing."""
        return CacheService(redis_url="redis://localhost:6379/0", ttl=3600)

    @pytest.fixture
    def sample_flight_events(self):
        """Sample flight events for testing."""
        return [
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            ),
            FlightEvent(
                flight_number="XX5678",
                from_city="BCN",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 14, 0),
                arrival_time=datetime(2024, 12, 25, 15, 15)
            )
        ]

    def test_get_cache_key(self, cache_service):
        """Test cache key generation."""
        search_date = date(2024, 12, 25)
        expected_key = "flight_events:2024-12-25"
        
        actual_key = cache_service._get_cache_key(search_date)
        assert actual_key == expected_key

    @pytest.mark.asyncio
    async def test_get_flight_events_cache_hit(self, cache_service, sample_flight_events):
        """Test retrieving flight events from cache (cache hit)."""
        # Mock Redis connection and response
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis
        
        # Mock cached data
        cached_data = json.dumps([
            {
                'flight_number': 'XX1234',
                'from_city': 'MAD',
                'to_city': 'BCN',
                'departure_time': '2024-12-25T10:00:00',
                'arrival_time': '2024-12-25T11:30:00'
            },
            {
                'flight_number': 'XX5678',
                'from_city': 'BCN',
                'to_city': 'PMI',
                'departure_time': '2024-12-25T14:00:00',
                'arrival_time': '2024-12-25T15:15:00'
            }
        ])
        mock_redis.get.return_value = cached_data
        
        # Test cache retrieval
        search_date = date(2024, 12, 25)
        result = await cache_service.get_flight_events(search_date)
        
        # Verify results
        assert result is not None
        assert len(result) == 2
        assert result[0].flight_number == "XX1234"
        assert result[1].flight_number == "XX5678"
        
        # Verify Redis was called correctly
        mock_redis.get.assert_called_once_with("flight_events:2024-12-25")

    @pytest.mark.asyncio
    async def test_get_flight_events_cache_miss(self, cache_service):
        """Test retrieving flight events from cache (cache miss)."""
        # Mock Redis connection
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis
        mock_redis.get.return_value = None
        
        # Test cache retrieval
        search_date = date(2024, 12, 25)
        result = await cache_service.get_flight_events(search_date)
        
        # Verify results
        assert result is None
        mock_redis.get.assert_called_once_with("flight_events:2024-12-25")

    @pytest.mark.asyncio
    async def test_get_flight_events_redis_error(self, cache_service):
        """Test handling Redis errors during retrieval."""
        # Mock Redis connection to raise an exception
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis
        mock_redis.get.side_effect = Exception("Redis connection error")
        
        # Test cache retrieval
        search_date = date(2024, 12, 25)
        result = await cache_service.get_flight_events(search_date)
        
        # Verify error handling
        assert result is None

    @pytest.mark.asyncio
    async def test_set_flight_events_success(self, cache_service, sample_flight_events):
        """Test storing flight events in cache successfully."""
        # Mock Redis connection
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis
        mock_redis.setex.return_value = True
        
        # Test cache storage
        search_date = date(2024, 12, 25)
        result = await cache_service.set_flight_events(search_date, sample_flight_events)
        
        # Verify results
        assert result is True
        
        # Verify Redis was called with correct parameters
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "flight_events:2024-12-25"  # key
        assert call_args[0][1] == 3600  # ttl
        
        # Verify the cached data structure
        cached_data = json.loads(call_args[0][2])
        assert len(cached_data) == 2
        assert cached_data[0]['flight_number'] == "XX1234"
        assert cached_data[1]['flight_number'] == "XX5678"

    @pytest.mark.asyncio
    async def test_set_flight_events_redis_error(self, cache_service, sample_flight_events):
        """Test handling Redis errors during storage."""
        # Mock Redis connection to raise an exception
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis
        mock_redis.setex.side_effect = Exception("Redis storage error")
        
        # Test cache storage
        search_date = date(2024, 12, 25)
        result = await cache_service.set_flight_events(search_date, sample_flight_events)
        
        # Verify error handling
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_flight_events_success(self, cache_service):
        """Test deleting flight events from cache successfully."""
        # Mock Redis connection
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis
        mock_redis.delete.return_value = 1  # 1 key deleted
        
        # Test cache deletion
        search_date = date(2024, 12, 25)
        result = await cache_service.delete_flight_events(search_date)
        
        # Verify results
        assert result is True
        mock_redis.delete.assert_called_once_with("flight_events:2024-12-25")

    @pytest.mark.asyncio
    async def test_delete_flight_events_not_found(self, cache_service):
        """Test deleting non-existent flight events from cache."""
        # Mock Redis connection
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis
        mock_redis.delete.return_value = 0  # No keys deleted
        
        # Test cache deletion
        search_date = date(2024, 12, 25)
        result = await cache_service.delete_flight_events(search_date)
        
        # Verify results
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_all_cache_success(self, cache_service):
        """Test clearing all flight event cache successfully."""
        # Mock Redis connection
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis
        mock_redis.keys.return_value = [
            "flight_events:2024-12-25",
            "flight_events:2024-12-26",
            "flight_events:2024-12-27"
        ]
        mock_redis.delete.return_value = 3  # 3 keys deleted
        
        # Test cache clearing
        result = await cache_service.clear_all_cache()
        
        # Verify results
        assert result is True
        mock_redis.keys.assert_called_once_with("flight_events:*")
        mock_redis.delete.assert_called_once_with(
            "flight_events:2024-12-25",
            "flight_events:2024-12-26", 
            "flight_events:2024-12-27"
        )

    @pytest.mark.asyncio
    async def test_clear_all_cache_empty(self, cache_service):
        """Test clearing cache when no entries exist."""
        # Mock Redis connection
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis
        mock_redis.keys.return_value = []  # No keys found
        
        # Test cache clearing
        result = await cache_service.clear_all_cache()
        
        # Verify results
        assert result is True
        mock_redis.keys.assert_called_once_with("flight_events:*")
        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_connection(self, cache_service):
        """Test closing Redis connection."""
        # Mock Redis connection
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis
        
        # Test connection closing
        await cache_service.close()
        
        # Verify connection was closed
        mock_redis.close.assert_called_once()
        assert cache_service._redis is None

    @pytest.mark.asyncio
    async def test_close_connection_no_connection(self, cache_service):
        """Test closing connection when no connection exists."""
        # Ensure no Redis connection
        cache_service._redis = None
        
        # Test connection closing (should not raise exception)
        await cache_service.close()
        
        # Verify no exception was raised
        assert cache_service._redis is None

    @pytest.mark.asyncio
    async def test_lazy_redis_initialization(self, cache_service):
        """Test that Redis connection is initialized lazily."""
        # Ensure no Redis connection initially
        assert cache_service._redis is None
        
        # Mock aioredis.from_url
        with patch('aioredis.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis
            mock_redis.get.return_value = None
            
            # Trigger Redis connection
            search_date = date(2024, 12, 25)
            await cache_service.get_flight_events(search_date)
            
            # Verify Redis was initialized
            mock_from_url.assert_called_once_with("redis://localhost:6379/0", decode_responses=True)
            assert cache_service._redis is not None
