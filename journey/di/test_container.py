"""
Tests for DI Container
"""
from unittest.mock import patch

from .container import DIContainer, get_container, reset_container
from ..core.services.journey_service import JourneyService
from ..infrastructure.adapters.flight_api_adapter import FlightApiAdapter


class TestDIContainer:
    """Test cases for DIContainer"""
    
    def setup_method(self):
        """Reset container before each test"""
        reset_container()
    
    def test_container_singleton(self):
        """Test that get_container returns the same instance"""
        container1 = get_container()
        container2 = get_container()
        
        assert container1 is container2
        assert isinstance(container1, DIContainer)
    
    def test_flight_api_adapter_singleton(self):
        """Test that flight_api_adapter is a singleton"""
        container = get_container()
        
        adapter1 = container.flight_api_adapter
        adapter2 = container.flight_api_adapter
        
        assert adapter1 is adapter2
        assert isinstance(adapter1, FlightApiAdapter)
    
    def test_journey_service_factory(self):
        """Test that create_journey_service creates new instances"""
        container = get_container()
        
        service1 = container.create_journey_service()
        service2 = container.create_journey_service()
        
        # Services should be different instances (factory pattern)
        assert service1 is not service2
        assert isinstance(service1, JourneyService)
        assert isinstance(service2, JourneyService)
        
        # But they should share the same flight_api_adapter (singleton)
        assert service1._flight_events_port is service2._flight_events_port
    
    @patch('journey.di.container.settings')
    def test_container_uses_custom_api_url(self, mock_settings):
        """Test that container uses custom API URL from settings"""
        mock_settings.FLIGHT_API_URL = 'http://test-api.com/flights'
        
        # Reset to force new container creation with new config
        reset_container()
        container = get_container()
        
        # Check that custom URL is used
        api_url = container._get_flight_api_url()
        assert api_url == 'http://test-api.com/flights'
    
    @patch('journey.di.container.settings')
    def test_container_uses_default_api_url(self, mock_settings):
        """Test that container uses default API URL when not configured"""
        # Simulate settings without FLIGHT_API_URL
        if hasattr(mock_settings, 'FLIGHT_API_URL'):
            delattr(mock_settings, 'FLIGHT_API_URL')
        
        reset_container()
        container = get_container()
        
        api_url = container._get_flight_api_url()
        assert 'mock.apidog.com' in api_url
    
    def test_reset_container(self):
        """Test that reset_container works correctly"""
        container1 = get_container()
        
        # Access adapter to create it
        adapter1 = container1.flight_api_adapter
        
        reset_container()
        container2 = get_container()
        
        # Should be a new container instance
        assert container1 is not container2
        
        # And new adapter instance
        adapter2 = container2.flight_api_adapter
        assert adapter1 is not adapter2
    
    def test_container_reset_method(self):
        """Test that container.reset() clears singletons"""
        container = get_container()
        
        # Create adapter
        adapter1 = container.flight_api_adapter
        
        # Reset the container
        container.reset()
        
        # Should create a new adapter
        adapter2 = container.flight_api_adapter
        assert adapter1 is not adapter2
