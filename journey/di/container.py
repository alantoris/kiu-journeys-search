"""
Simple Dependency Injection Container
"""
from typing import Optional
from django.conf import settings

from ..core.services.journey_service import JourneyService
from ..infrastructure.adapters.flight_api_adapter import FlightApiAdapter
from ..infrastructure.adapters.cache_service import CacheService


class DIContainer:
    """
    Simple DI Container for managing application dependencies.
    """
    
    def __init__(self):
        self._flight_api_adapter: Optional[FlightApiAdapter] = None
        self._cache_service: Optional[CacheService] = None
    
    def _get_flight_api_url(self) -> str:
        """Get flight API URL from settings"""
        return getattr(
            settings, 
            'FLIGHT_API_URL', 
            'https://mock.apidog.com/m1/814105-793312-default/flight-events'
        )
    
    @property
    def cache_service(self) -> CacheService:
        """Get CacheService instance (Singleton)"""
        if self._cache_service is None:
            self._cache_service = CacheService()
        return self._cache_service
    
    @property
    def flight_api_adapter(self) -> FlightApiAdapter:
        """Get FlightApiAdapter instance (Singleton)"""
        if self._flight_api_adapter is None:
            self._flight_api_adapter = FlightApiAdapter(
                api_url=self._get_flight_api_url(),
                cache_service=self.cache_service
            )
        return self._flight_api_adapter
    
    def create_journey_service(self) -> JourneyService:
        """Create JourneyService instance"""
        return JourneyService(
            flight_events_port=self.flight_api_adapter
        )
    
    def reset(self):
        """Reset singleton instances (useful for testing)"""
        self._flight_api_adapter = None
        self._cache_service = None


# Global container instance
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Get the global DI container instance"""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def reset_container():
    """Reset the global container (useful for testing)"""
    global _container
    if _container:
        _container.reset()
    _container = None
