"""
Domain interfaces - Ports for hexagonal architecture
"""
from abc import ABC, abstractmethod
from typing import List
from datetime import date

from .entities.flight_event import FlightEvent


class FlightEventsPort(ABC):
    """
    Port interface for accessing flight events from external services.
    This defines the contract that adapters must implement.
    """
    
    @abstractmethod
    async def get_flight_events(self, search_date: date) -> List[FlightEvent]:
        """
        Get all flight events for a specific date.
        
        Args:
            search_date: The date to search for flight events
            
        Returns:
            List of flight events available on the given date
        """
        pass
