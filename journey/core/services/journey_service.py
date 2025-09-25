"""
Journey Service - Core business logic for journey operations
"""
from typing import List
from datetime import date

from ..entities.flight_event import FlightEvent, Journey
from ..interfaces import FlightEventsPort


class JourneyService:
    """
    Core domain service for journey search operations.
    Contains pure business logic for finding journeys between cities.
    """
    
    def __init__(self, flight_events_port: FlightEventsPort):
        self._flight_events_port = flight_events_port
    
    async def search_journeys(
        self,
        search_date: date,
        from_city: str,
        to_city: str
    ) -> List[Journey]:
        """
        Search for all possible journeys from origin to destination on a given date.
        
        Currently supports direct flights (1 flight) and one-connection flights (2 flights).
        
        Args:
            search_date: Date to search for journeys
            from_city: Origin city (3-letter code)
            to_city: Destination city (3-letter code)
            
        Returns:
            List of valid journeys (direct flights + 1-connection flights)
            
        Note: v1.0 limitation - only supports journeys with max 2 flights.
        Future versions will support multi-leg journeys.
        """
        # Get all flight events for the date
        flight_events = await self._flight_events_port.get_flight_events(search_date)
        
        journeys = []
        
        # Find direct flights (0 connections)
        direct_journeys = self._find_direct_journeys(flight_events, from_city, to_city)
        journeys.extend(direct_journeys)
        
        # Find connecting flights (1 connection)
        connecting_journeys = self._find_connecting_journeys(flight_events, from_city, to_city)
        journeys.extend(connecting_journeys)
        
        # Sort by departure time
        journeys.sort(key=lambda j: j.departure_time)
        
        return journeys
    
    def _find_direct_journeys(
        self,
        flight_events: List[FlightEvent],
        from_city: str,
        to_city: str
    ) -> List[Journey]:
        """Find direct flights (no connections)"""
        direct_journeys = []
        
        for flight in flight_events:
            if flight.from_city == from_city and flight.to_city == to_city:
                try:
                    journey = Journey(path=[flight])
                    direct_journeys.append(journey)
                except ValueError:
                    # Skip invalid journeys (shouldn't happen for single flights)
                    continue
        
        return direct_journeys
    
    def _find_connecting_journeys(
        self,
        flight_events: List[FlightEvent],
        from_city: str,
        to_city: str
    ) -> List[Journey]:
        """Find journeys with exactly 1 connection"""
        connecting_journeys = []
        
        # Find all flights departing from origin
        first_leg_flights = [
            flight for flight in flight_events 
            if flight.from_city == from_city
        ]
        
        # Find all flights arriving at destination
        second_leg_flights = [
            flight for flight in flight_events 
            if flight.to_city == to_city
        ]
        
        # Try all combinations
        for first_flight in first_leg_flights:
            for second_flight in second_leg_flights:
                # Check if flights can be connected
                if (first_flight.to_city == second_flight.from_city and
                    first_flight.to_city != to_city):  # Avoid direct flights
                    
                    try:
                        journey = Journey(path=[first_flight, second_flight])
                        connecting_journeys.append(journey)
                    except ValueError:
                        # Skip invalid connections (timing, duration, etc.)
                        continue
        
        return connecting_journeys
