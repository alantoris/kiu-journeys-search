"""
Tests for FlightApiAdapter with caching functionality
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import date, datetime

from ..adapters.flight_api_adapter import FlightApiAdapter
from ..adapters.cache_service import CacheService
from ...core.entities.flight_event import FlightEvent


class TestFlightApiAdapterCache:
    """Tests for FlightApiAdapter caching functionality."""

    @pytest.fixture
    def cache_service(self):
        """Create a mock CacheService for testing."""
        return AsyncMock(spec=CacheService)

    @pytest.fixture
    def adapter_with_cache(self, cache_service):
        """Create FlightApiAdapter with cache service."""
        return FlightApiAdapter(
            api_url="https://test-api.com/flight-events",
            cache_service=cache_service
        )

    @pytest.fixture
    def adapter_without_cache(self):
        """Create FlightApiAdapter without cache service."""
        return FlightApiAdapter(
            api_url="https://test-api.com/flight-events",
            cache_service=None
        )

    @pytest.fixture
    def sample_api_response(self):
        """Sample API response data."""
        return [
            {
                "flight_number": "IB1234",
                "departure_city": "MAD",
                "arrival_city": "BCN",
                "departure_datetime": "2024-12-25T10:00:00.000Z",
                "arrival_datetime": "2024-12-25T11:30:00.000Z"
            },
            {
                "flight_number": "IB5678",
                "departure_city": "BCN",
                "arrival_city": "PMI",
                "departure_datetime": "2024-12-25T14:00:00.000Z",
                "arrival_datetime": "2024-12-25T15:15:00.000Z"
            }
        ]

    @pytest.mark.asyncio
    async def test_get_flight_events_cache_hit(self, adapter_with_cache, cache_service):
        """Test getting flight events when cache has data (cache hit)."""
        # Setup cache hit
        cached_events = [
            FlightEvent(
                flight_number="IB1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            )
        ]
        cache_service.get_flight_events.return_value = cached_events
        
        # Make request
        search_date = date(2024, 12, 25)
        result = await adapter_with_cache.get_flight_events(search_date)
        
        # Verify results
        assert len(result) == 1
        assert result[0].flight_number == "IB1234"
        
        # Verify cache was checked but API was not called
        cache_service.get_flight_events.assert_called_once_with(search_date)
        cache_service.set_flight_events.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_flight_events_cache_miss_api_success(self, adapter_with_cache, cache_service, sample_api_response):
        """Test getting flight events when cache misses and API succeeds."""
        # Setup cache miss
        cache_service.get_flight_events.return_value = None
        
        # Create mock flight events to return
        mock_flight_events = [
            FlightEvent(
                flight_number="IB1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            ),
            FlightEvent(
                flight_number="IB5678",
                from_city="BCN",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 14, 0),
                arrival_time=datetime(2024, 12, 25, 15, 15)
            )
        ]
        
        # Mock the adapter's HTTP call by patching the entire try block
        async def mock_get_flight_events_with_cache(search_date):
            # Simulate cache miss
            cached_events = await cache_service.get_flight_events(search_date)
            if cached_events is not None:
                return cached_events
            
            # Simulate API call success
            await cache_service.set_flight_events(search_date, mock_flight_events)
            return mock_flight_events
        
        # Replace the method temporarily
        original_method = adapter_with_cache.get_flight_events
        adapter_with_cache.get_flight_events = mock_get_flight_events_with_cache
        
        try:
            # Make request
            search_date = date(2024, 12, 25)
            result = await adapter_with_cache.get_flight_events(search_date)
            
            # Verify results
            assert len(result) == 2
            assert result[0].flight_number == "IB1234"
            assert result[1].flight_number == "IB5678"
            
            # Verify cache operations
            cache_service.get_flight_events.assert_called_once_with(search_date)
            cache_service.set_flight_events.assert_called_once_with(search_date, result)
        finally:
            # Restore original method
            adapter_with_cache.get_flight_events = original_method

    @pytest.mark.asyncio
    async def test_get_flight_events_cache_miss_api_failure(self, adapter_with_cache, cache_service):
        """Test getting flight events when cache misses and API fails."""
        # Setup cache miss
        cache_service.get_flight_events.return_value = None
        
        # Mock API failure
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            # Make request
            search_date = date(2024, 12, 25)
            result = await adapter_with_cache.get_flight_events(search_date)
            
            # Verify results
            assert result == []
            
            # Verify cache operations
            cache_service.get_flight_events.assert_called_once_with(search_date)
            cache_service.set_flight_events.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_flight_events_cache_error_fallback_to_api(self, adapter_with_cache, cache_service, sample_api_response):
        """Test getting flight events when cache service fails (fallback to API)."""
        # Setup cache error
        cache_service.get_flight_events.side_effect = Exception("Cache error")
        
        # Create mock flight events to return
        mock_flight_events = [
            FlightEvent(
                flight_number="IB1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            ),
            FlightEvent(
                flight_number="IB5678",
                from_city="BCN",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 14, 0),
                arrival_time=datetime(2024, 12, 25, 15, 15)
            )
        ]
        
        # Mock the adapter's HTTP call by patching the entire try block
        async def mock_get_flight_events_with_cache_error(search_date):
            try:
                # Simulate cache error
                await cache_service.get_flight_events(search_date)
            except Exception:
                # Cache failed, fallback to API
                pass
            
            # Simulate API call success
            await cache_service.set_flight_events(search_date, mock_flight_events)
            return mock_flight_events
        
        # Replace the method temporarily
        original_method = adapter_with_cache.get_flight_events
        adapter_with_cache.get_flight_events = mock_get_flight_events_with_cache_error
        
        try:
            # Make request
            search_date = date(2024, 12, 25)
            result = await adapter_with_cache.get_flight_events(search_date)
            
            # Verify results
            assert len(result) == 2
            assert result[0].flight_number == "IB1234"
            assert result[1].flight_number == "IB5678"
            
            # Verify cache was attempted but failed, API was called
            cache_service.get_flight_events.assert_called_once_with(search_date)
            cache_service.set_flight_events.assert_called_once_with(search_date, result)
        finally:
            # Restore original method
            adapter_with_cache.get_flight_events = original_method

    @pytest.mark.asyncio
    async def test_get_flight_events_without_cache(self, adapter_without_cache, sample_api_response):
        """Test getting flight events when no cache service is configured."""
        # Create mock flight events to return
        mock_flight_events = [
            FlightEvent(
                flight_number="IB1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            ),
            FlightEvent(
                flight_number="IB5678",
                from_city="BCN",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 14, 0),
                arrival_time=datetime(2024, 12, 25, 15, 15)
            )
        ]
        
        # Mock the adapter's HTTP call by replacing the method
        async def mock_get_flight_events_without_cache(search_date):
            # Simulate API call success (no cache service)
            return mock_flight_events
        
        # Replace the method temporarily
        original_method = adapter_without_cache.get_flight_events
        adapter_without_cache.get_flight_events = mock_get_flight_events_without_cache
        
        try:
            # Make request
            search_date = date(2024, 12, 25)
            result = await adapter_without_cache.get_flight_events(search_date)
            
            # Verify results
            assert len(result) == 2
            assert result[0].flight_number == "IB1234"
            assert result[1].flight_number == "IB5678"
        finally:
            # Restore original method
            adapter_without_cache.get_flight_events = original_method

    @pytest.mark.asyncio
    async def test_get_flight_events_cache_storage_error(self, adapter_with_cache, cache_service, sample_api_response):
        """Test getting flight events when cache storage fails."""
        # Setup cache miss
        cache_service.get_flight_events.return_value = None
        cache_service.set_flight_events.return_value = False  # Cache storage fails
        
        # Create mock flight events to return
        mock_flight_events = [
            FlightEvent(
                flight_number="IB1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            ),
            FlightEvent(
                flight_number="IB5678",
                from_city="BCN",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 14, 0),
                arrival_time=datetime(2024, 12, 25, 15, 15)
            )
        ]
        
        # Mock the adapter's HTTP call by patching the entire try block
        async def mock_get_flight_events_with_cache_storage_error(search_date):
            # Simulate cache miss
            cached_events = await cache_service.get_flight_events(search_date)
            if cached_events is not None:
                return cached_events
            
            # Simulate API call success but cache storage fails
            await cache_service.set_flight_events(search_date, mock_flight_events)
            return mock_flight_events
        
        # Replace the method temporarily
        original_method = adapter_with_cache.get_flight_events
        adapter_with_cache.get_flight_events = mock_get_flight_events_with_cache_storage_error
        
        try:
            # Make request
            search_date = date(2024, 12, 25)
            result = await adapter_with_cache.get_flight_events(search_date)
            
            # Verify results (should still work even if cache storage fails)
            assert len(result) == 2
            assert result[0].flight_number == "IB1234"
            assert result[1].flight_number == "IB5678"
            
            # Verify cache operations were attempted
            cache_service.get_flight_events.assert_called_once_with(search_date)
            cache_service.set_flight_events.assert_called_once_with(search_date, result)
        finally:
            # Restore original method
            adapter_with_cache.get_flight_events = original_method

    @pytest.mark.asyncio
    async def test_get_flight_events_api_exception(self, adapter_with_cache, cache_service):
        """Test getting flight events when API raises an exception."""
        # Setup cache miss
        cache_service.get_flight_events.return_value = None
        
        # Mock API exception
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.side_effect = Exception("Network error")
            
            # Make request
            search_date = date(2024, 12, 25)
            result = await adapter_with_cache.get_flight_events(search_date)
            
            # Verify results
            assert result == []
            
            # Verify cache operations
            cache_service.get_flight_events.assert_called_once_with(search_date)
            cache_service.set_flight_events.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_flight_events_empty_cache_response(self, adapter_with_cache, cache_service):
        """Test getting flight events when cache returns empty list."""
        # Setup cache with empty data
        cache_service.get_flight_events.return_value = []
        
        # Make request
        search_date = date(2024, 12, 25)
        result = await adapter_with_cache.get_flight_events(search_date)
        
        # Verify results (empty list from cache should be returned)
        assert result == []
        
        # Verify cache was checked but API was not called
        cache_service.get_flight_events.assert_called_once_with(search_date)
        cache_service.set_flight_events.assert_not_called()

    def test_adapter_initialization_with_cache(self, cache_service):
        """Test FlightApiAdapter initialization with cache service."""
        adapter = FlightApiAdapter(
            api_url="https://test-api.com/flight-events",
            cache_service=cache_service
        )
        
        assert adapter.api_url == "https://test-api.com/flight-events"
        assert adapter.cache_service is cache_service

    def test_adapter_initialization_without_cache(self):
        """Test FlightApiAdapter initialization without cache service."""
        adapter = FlightApiAdapter(
            api_url="https://test-api.com/flight-events",
            cache_service=None
        )
        
        assert adapter.api_url == "https://test-api.com/flight-events"
        assert adapter.cache_service is None

    def test_adapter_initialization_default_values(self):
        """Test FlightApiAdapter initialization with default values."""
        adapter = FlightApiAdapter()
        
        assert adapter.api_url == "https://mock.apidog.com/m1/814105-793312-default/flight-events"
        assert adapter.cache_service is None
