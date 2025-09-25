"""
Flight Event Entity - Domain model for flight events
"""
from dataclasses import dataclass
from datetime import datetime

from ..config import MAX_FLIGHTS_PER_JOURNEY, MAX_JOURNEY_DURATION_HOURS, MAX_CONNECTION_TIME_HOURS


@dataclass
class FlightEvent:
    """
    Domain entity representing a flight event.
    Represents a specific instance of a flight on a particular date.
    """
    flight_number: str
    from_city: str  # 3-letter city code
    to_city: str    # 3-letter city code
    departure_time: datetime  # UTC
    arrival_time: datetime    # UTC
    
    def __post_init__(self):
        """Validate business rules"""
        if self.departure_time >= self.arrival_time:
            raise ValueError("Departure time must be before arrival time")
        
        if not self.flight_number.strip():
            raise ValueError("Flight number cannot be empty")
        
        if len(self.from_city) != 3 or len(self.to_city) != 3:
            raise ValueError("City codes must be exactly 3 characters")
        
        if self.from_city == self.to_city:
            raise ValueError("Origin and destination cities cannot be the same")
    
    @property
    def duration_minutes(self) -> int:
        """Calculate flight duration in minutes"""
        delta = self.arrival_time - self.departure_time
        return int(delta.total_seconds() / 60)


@dataclass
class Journey:
    """
    Domain entity representing a journey (sequence of flight events).
    A journey connects an origin to a destination with 1 or 2 flight events.
    
    Business rules:
    - Must have at least 1 flight event
    - Maximum 2 flight events (v1.0 limitation - future versions will support more)
    - If multiple flights, destination of first must match origin of second
    - Connection time between flights must be <= 4 hours (configurable in v2.0+)
    - Total journey duration must be <= 24 hours (configurable in v2.0+)
    
    Note: The 2-flight limitation is specific to v1.0. Future versions will
    support multi-leg journeys with more than 2 flights.
    """
    path: list[FlightEvent]
    
    def __post_init__(self):
        """Validate business rules"""
        if not self.path:
            raise ValueError("Journey must have at least one flight event")
        
        if len(self.path) > MAX_FLIGHTS_PER_JOURNEY:
            raise ValueError(f"Journey cannot have more than {MAX_FLIGHTS_PER_JOURNEY} flight events (v1.0 limitation)")
        
        # Validate connection if multiple flights
        if len(self.path) > 1:
            self._validate_connection()
        
        # Validate total duration
        if self.total_duration_hours > MAX_JOURNEY_DURATION_HOURS:
            raise ValueError(f"Journey cannot exceed {MAX_JOURNEY_DURATION_HOURS} hours (v1.0 limitation)")
    
    def _validate_connection(self):
        """Validate connection between flights"""
        for i in range(len(self.path) - 1):
            current_flight = self.path[i]
            next_flight = self.path[i + 1]
            
            # Check that destination of current flight matches origin of next flight
            if current_flight.to_city != next_flight.from_city:
                raise ValueError(
                    f"Flight connection invalid: {current_flight.to_city} -> {next_flight.from_city}"
                )
            
            # Check connection time (v1.0 limit)
            connection_time = next_flight.departure_time - current_flight.arrival_time
            connection_hours = connection_time.total_seconds() / 3600
            
            if connection_hours > MAX_CONNECTION_TIME_HOURS:
                raise ValueError(
                    f"Connection time cannot exceed {MAX_CONNECTION_TIME_HOURS} hours (v1.0 limitation). Current: {connection_hours:.1f}h"
                )
            
            if connection_hours < 0:
                raise ValueError("Next flight departs before current flight arrives")
    
    @property
    def connections(self) -> int:
        """Number of connections (flight events - 1)"""
        return len(self.path) - 1
    
    @property
    def origin(self) -> str:
        """Origin city of the journey"""
        return self.path[0].from_city
    
    @property
    def destination(self) -> str:
        """Destination city of the journey"""
        return self.path[-1].to_city
    
    @property
    def departure_time(self) -> datetime:
        """Departure time of the first flight"""
        return self.path[0].departure_time
    
    @property
    def arrival_time(self) -> datetime:
        """Arrival time of the last flight"""
        return self.path[-1].arrival_time
    
    @property
    def total_duration_hours(self) -> float:
        """Total journey duration in hours"""
        delta = self.arrival_time - self.departure_time
        return delta.total_seconds() / 3600
