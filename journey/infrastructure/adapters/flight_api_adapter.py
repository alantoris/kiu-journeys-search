"""
Flight API Adapter - Infrastructure implementation for external flight APIs
"""
import aiohttp
from typing import List, Optional
from datetime import date, datetime
import logging

from ...core.interfaces import FlightEventsPort
from ...core.entities.flight_event import FlightEvent
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class FlightApiAdapter(FlightEventsPort):
    """
    Adapter that implements FlightEventsPort interface.
    Consumes the external flight events API with caching support.
    """
    
    def __init__(self, api_url: str = None, cache_service: Optional[CacheService] = None):
        self.api_url = api_url or "https://mock.apidog.com/m1/814105-793312-default/flight-events"
        self.cache_service = cache_service
    
    async def get_flight_events(self, search_date: date) -> List[FlightEvent]:
        """
        Get all flight events for a specific date from cache or external API.
        
        First checks cache, if not found, fetches from API and caches the result.
        
        Args:
            search_date: The date to search for flight events
            
        Returns:
            List of flight events available on the given date
        """
        # Try to get from cache first
        if self.cache_service:
            cached_events = await self.cache_service.get_flight_events(search_date)
            if cached_events is not None:
                logger.info(f"Returning {len(cached_events)} flight events from cache for {search_date}")
                return cached_events
        
        # Cache miss or no cache service - fetch from API
        logger.info(f"Fetching flight events from API for {search_date}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        flight_events = self._parse_flight_events(data, search_date)
                        
                        # Cache the results if cache service is available
                        if self.cache_service and flight_events:
                            await self.cache_service.set_flight_events(search_date, flight_events)
                        
                        logger.info(f"Fetched {len(flight_events)} flight events from API for {search_date}")
                        return flight_events
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching flight events: {str(e)}")
            return []
    
    def _parse_flight_events(self, api_data: dict, search_date: date) -> List[FlightEvent]:
        """
        Parse API response data into FlightEvent domain entities.
        
        Args:
            api_data: Raw API response data
            search_date: Date to filter events for
            
        Returns:
            List of FlightEvent objects
        """
        flight_events = []
        
        # Assuming the API returns a list of flight events
        # The exact structure depends on the actual API response
        events = api_data if isinstance(api_data, list) else api_data.get('events', [])
        
        for event_data in events:
            try:
                # Parse the flight event data
                flight_event = self._create_flight_event_from_api_data(event_data, search_date)
                if flight_event:
                    flight_events.append(flight_event)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid flight event: {str(e)}")
                continue
        
        return flight_events
    
    def _create_flight_event_from_api_data(self, event_data: dict, search_date: date) -> FlightEvent:
        """
        Create a FlightEvent from API data.
        
        Actual API data structure:
        {
            "flight_number": "IB1234",
            "departure_city": "MAD",
            "arrival_city": "BUE",
            "departure_datetime": "2021-12-31T23:59:59.000Z",
            "arrival_datetime": "2022-01-01T12:00:00.000Z"
        }
        """
        # Parse departure and arrival times
        departure_str = event_data['departure_datetime']
        arrival_str = event_data['arrival_datetime']
        
        # Convert to datetime objects (assuming UTC)
        departure_time = datetime.fromisoformat(departure_str.replace('Z', '+00:00'))
        arrival_time = datetime.fromisoformat(arrival_str.replace('Z', '+00:00'))
        
        # Filter by date - only include flights that depart on the search date
        if departure_time.date() != search_date:
            return None
        
        return FlightEvent(
            flight_number=event_data['flight_number'],
            from_city=event_data['departure_city'],
            to_city=event_data['arrival_city'],
            departure_time=departure_time,
            arrival_time=arrival_time
        )
