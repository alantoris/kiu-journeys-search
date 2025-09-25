"""
Tests for domain entities
"""
from datetime import datetime
from django.test import TestCase

from ..entities.flight_event import FlightEvent, Journey
from ..config import MAX_FLIGHTS_PER_JOURNEY, MAX_JOURNEY_DURATION_HOURS, MAX_CONNECTION_TIME_HOURS


class TestFlightEvent(TestCase):
    """Tests for FlightEvent entity."""

    def test_valid_flight_event_creation(self):
        """Test creating a valid flight event."""
        flight = FlightEvent(
            flight_number="XX1234",
            from_city="MAD",
            to_city="BCN",
            departure_time=datetime(2024, 12, 25, 10, 0),
            arrival_time=datetime(2024, 12, 25, 11, 30)
        )
        
        self.assertEqual(flight.flight_number, "XX1234")
        self.assertEqual(flight.from_city, "MAD")
        self.assertEqual(flight.to_city, "BCN")
        self.assertEqual(flight.departure_time, datetime(2024, 12, 25, 10, 0))
        self.assertEqual(flight.arrival_time, datetime(2024, 12, 25, 11, 30))

    def test_duration_calculation(self):
        """Test flight duration calculation."""
        flight = FlightEvent(
            flight_number="XX1234",
            from_city="MAD",
            to_city="BCN",
            departure_time=datetime(2024, 12, 25, 10, 0),
            arrival_time=datetime(2024, 12, 25, 11, 30)  # 90 minutes
        )
        
        self.assertEqual(flight.duration_minutes, 90)

    def test_duration_calculation_cross_day(self):
        """Test flight duration calculation across days."""
        flight = FlightEvent(
            flight_number="XX1234",
            from_city="MAD",
            to_city="NYC",
            departure_time=datetime(2024, 12, 25, 23, 0),
            arrival_time=datetime(2024, 12, 26, 6, 30)  # 7.5 hours = 450 minutes
        )
        
        self.assertEqual(flight.duration_minutes, 450)

    def test_invalid_departure_after_arrival(self):
        """Test that departure time must be before arrival time."""
        with self.assertRaises(ValueError) as context:
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 11, 30),
                arrival_time=datetime(2024, 12, 25, 10, 0)  # Before departure
            )
        
        self.assertIn("Departure time must be before arrival time", str(context.exception))

    def test_same_departure_arrival_time(self):
        """Test that departure and arrival cannot be the same time."""
        with self.assertRaises(ValueError) as context:
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 10, 0)  # Same time
            )
        
        self.assertIn("Departure time must be before arrival time", str(context.exception))

    def test_empty_flight_number(self):
        """Test that flight number cannot be empty."""
        with self.assertRaises(ValueError) as context:
            FlightEvent(
                flight_number="",  # Empty
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            )
        
        self.assertIn("Flight number cannot be empty", str(context.exception))

    def test_whitespace_flight_number(self):
        """Test that flight number cannot be only whitespace."""
        with self.assertRaises(ValueError) as context:
            FlightEvent(
                flight_number="   ",  # Only whitespace
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            )
        
        self.assertIn("Flight number cannot be empty", str(context.exception))

    def test_invalid_city_code_length(self):
        """Test that city codes must be exactly 3 characters."""
        # Too short
        with self.assertRaises(ValueError) as context:
            FlightEvent(
                flight_number="XX1234",
                from_city="MA",  # 2 chars
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            )
        
        self.assertIn("City codes must be exactly 3 characters", str(context.exception))
        
        # Too long
        with self.assertRaises(ValueError) as context:
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="BCNM",  # 4 chars
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            )
        
        self.assertIn("City codes must be exactly 3 characters", str(context.exception))

    def test_same_origin_destination(self):
        """Test that origin and destination cannot be the same."""
        with self.assertRaises(ValueError) as context:
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="MAD",  # Same city
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            )
        
        self.assertIn("Origin and destination cities cannot be the same", str(context.exception))

    def test_flight_number_with_spaces(self):
        """Test that flight number with spaces is valid (trimmed)."""
        flight = FlightEvent(
            flight_number=" XX1234 ",  # With spaces
            from_city="MAD",
            to_city="BCN",
            departure_time=datetime(2024, 12, 25, 10, 0),
            arrival_time=datetime(2024, 12, 25, 11, 30)
        )
        
        self.assertEqual(flight.flight_number, " XX1234 ")  # Should keep original


class TestJourney(TestCase):
    """Tests for Journey entity."""

    def setUp(self):
        """Set up test flight events."""
        self.flight1 = FlightEvent(
            flight_number="XX1234",
            from_city="MAD",
            to_city="BCN",
            departure_time=datetime(2024, 12, 25, 10, 0),
            arrival_time=datetime(2024, 12, 25, 11, 30)
        )
        
        self.flight2 = FlightEvent(
            flight_number="XX5678",
            from_city="BCN",
            to_city="PMI",
            departure_time=datetime(2024, 12, 25, 13, 0),
            arrival_time=datetime(2024, 12, 25, 14, 15)
        )

    def test_valid_direct_journey(self):
        """Test creating a valid direct journey (1 flight)."""
        journey = Journey(path=[self.flight1])
        
        self.assertEqual(journey.connections, 0)
        self.assertEqual(journey.origin, "MAD")
        self.assertEqual(journey.destination, "BCN")
        self.assertEqual(journey.departure_time, datetime(2024, 12, 25, 10, 0))
        self.assertEqual(journey.arrival_time, datetime(2024, 12, 25, 11, 30))
        self.assertAlmostEqual(journey.total_duration_hours, 1.5, places=2)

    def test_valid_connecting_journey(self):
        """Test creating a valid connecting journey (2 flights)."""
        journey = Journey(path=[self.flight1, self.flight2])
        
        self.assertEqual(journey.connections, 1)
        self.assertEqual(journey.origin, "MAD")
        self.assertEqual(journey.destination, "PMI")
        self.assertEqual(journey.departure_time, datetime(2024, 12, 25, 10, 0))
        self.assertEqual(journey.arrival_time, datetime(2024, 12, 25, 14, 15))
        self.assertAlmostEqual(journey.total_duration_hours, 4.25, places=2)

    def test_empty_journey_raises_error(self):
        """Test that empty journey raises error."""
        with self.assertRaises(ValueError) as context:
            Journey(path=[])
        
        self.assertIn("Journey must have at least one flight event", str(context.exception))

    def test_too_many_flights_raises_error(self):
        """Test that journey with more than MAX_FLIGHTS_PER_JOURNEY raises error."""
        # Create more flights than allowed
        flights = []
        for i in range(MAX_FLIGHTS_PER_JOURNEY + 1):
            flight = FlightEvent(
                flight_number=f"XX{i:04d}",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10 + i, 0),
                arrival_time=datetime(2024, 12, 25, 11 + i, 30)
            )
            flights.append(flight)
        
        with self.assertRaises(ValueError) as context:
            Journey(path=flights)
        
        self.assertIn(f"Journey cannot have more than {MAX_FLIGHTS_PER_JOURNEY} flight events", str(context.exception))

    def test_invalid_connection_cities(self):
        """Test that connection cities must match."""
        # Create flights with mismatched connection cities
        flight2_invalid = FlightEvent(
            flight_number="XX5678",
            from_city="PMI",  # Different from flight1.to_city (BCN)
            to_city="VAL",
            departure_time=datetime(2024, 12, 25, 13, 0),
            arrival_time=datetime(2024, 12, 25, 14, 15)
        )
        
        with self.assertRaises(ValueError) as context:
            Journey(path=[self.flight1, flight2_invalid])
        
        self.assertIn("Flight connection invalid: BCN -> PMI", str(context.exception))

    def test_connection_time_too_long(self):
        """Test that connection time cannot exceed MAX_CONNECTION_TIME_HOURS."""
        # Create flight with connection time > 4 hours
        flight2_late = FlightEvent(
            flight_number="XX5678",
            from_city="BCN",
            to_city="PMI",
            departure_time=datetime(2024, 12, 25, 16, 0),  # 5 hours after flight1 arrival
            arrival_time=datetime(2024, 12, 25, 17, 15)
        )
        
        with self.assertRaises(ValueError) as context:
            Journey(path=[self.flight1, flight2_late])
        
        self.assertIn(f"Connection time cannot exceed {MAX_CONNECTION_TIME_HOURS} hours", str(context.exception))

    def test_connection_time_exactly_at_limit(self):
        """Test that connection time exactly at limit is valid."""
        # Create flight with connection time exactly 4 hours
        flight2_exact = FlightEvent(
            flight_number="XX5678",
            from_city="BCN",
            to_city="PMI",
            departure_time=datetime(2024, 12, 25, 15, 30),  # Exactly 4 hours after flight1 arrival
            arrival_time=datetime(2024, 12, 25, 16, 45)
        )
        
        journey = Journey(path=[self.flight1, flight2_exact])
        self.assertEqual(journey.connections, 1)

    def test_connection_time_negative(self):
        """Test that next flight cannot depart before current flight arrives."""
        # Create flight that departs before previous flight arrives
        flight2_early = FlightEvent(
            flight_number="XX5678",
            from_city="BCN",
            to_city="PMI",
            departure_time=datetime(2024, 12, 25, 10, 30),  # Before flight1 arrives
            arrival_time=datetime(2024, 12, 25, 11, 45)
        )
        
        with self.assertRaises(ValueError) as context:
            Journey(path=[self.flight1, flight2_early])
        
        self.assertIn("Next flight departs before current flight arrives", str(context.exception))

    def test_journey_duration_exceeds_limit(self):
        """Test that journey duration cannot exceed MAX_JOURNEY_DURATION_HOURS."""
        # Create flight with very long duration (> 24 hours)
        flight_long = FlightEvent(
            flight_number="XX1234",
            from_city="MAD",
            to_city="NYC",
            departure_time=datetime(2024, 12, 25, 10, 0),
            arrival_time=datetime(2024, 12, 26, 11, 0)  # 25 hours
        )
        
        with self.assertRaises(ValueError) as context:
            Journey(path=[flight_long])
        
        self.assertIn(f"Journey cannot exceed {MAX_JOURNEY_DURATION_HOURS} hours", str(context.exception))

    def test_journey_duration_exactly_at_limit(self):
        """Test that journey duration exactly at limit is valid."""
        # Create flight with duration exactly 24 hours
        flight_exact = FlightEvent(
            flight_number="XX1234",
            from_city="MAD",
            to_city="NYC",
            departure_time=datetime(2024, 12, 25, 10, 0),
            arrival_time=datetime(2024, 12, 26, 10, 0)  # Exactly 24 hours
        )
        
        journey = Journey(path=[flight_exact])
        self.assertEqual(journey.connections, 0)
        self.assertAlmostEqual(journey.total_duration_hours, 24.0, places=2)

    def test_multiple_connections_validation(self):
        """Test validation with multiple connections (if we had more than 2 flights)."""
        # This test documents the current limitation
        # In v1.0, we can only have 2 flights max, so this test validates that
        self.assertEqual(MAX_FLIGHTS_PER_JOURNEY, 2)
        
        # Test with exactly 2 flights (maximum allowed)
        journey = Journey(path=[self.flight1, self.flight2])
        self.assertEqual(journey.connections, 1)

    def test_journey_properties(self):
        """Test journey property calculations."""
        journey = Journey(path=[self.flight1, self.flight2])
        
        # Test properties
        self.assertEqual(journey.connections, 1)
        self.assertEqual(journey.origin, "MAD")
        self.assertEqual(journey.destination, "PMI")
        self.assertEqual(journey.departure_time, self.flight1.departure_time)
        self.assertEqual(journey.arrival_time, self.flight2.arrival_time)
        
        # Test total duration calculation
        expected_duration = (self.flight2.arrival_time - self.flight1.departure_time).total_seconds() / 3600
        self.assertAlmostEqual(journey.total_duration_hours, expected_duration, places=2)

    def test_connection_time_calculation_precision(self):
        """Test connection time calculation with high precision."""
        # Create flight with very precise connection time
        flight2_precise = FlightEvent(
            flight_number="XX5678",
            from_city="BCN",
            to_city="PMI",
            departure_time=datetime(2024, 12, 25, 11, 30, 30),  # 30 seconds after flight1
            arrival_time=datetime(2024, 12, 25, 12, 45)
        )
        
        journey = Journey(path=[self.flight1, flight2_precise])
        self.assertEqual(journey.connections, 1)
        
        # Connection time should be 0.008 hours (30 seconds)
        connection_time = flight2_precise.departure_time - self.flight1.arrival_time
        connection_hours = connection_time.total_seconds() / 3600
        self.assertAlmostEqual(connection_hours, 0.008, places=3)

    def test_journey_with_single_minute_duration(self):
        """Test journey with very short duration (1 minute)."""
        flight_short = FlightEvent(
            flight_number="XX1234",
            from_city="MAD",
            to_city="BCN",
            departure_time=datetime(2024, 12, 25, 10, 0),
            arrival_time=datetime(2024, 12, 25, 10, 1)  # 1 minute
        )
        
        journey = Journey(path=[flight_short])
        self.assertEqual(journey.connections, 0)
        self.assertAlmostEqual(journey.total_duration_hours, 1/60, places=4)  # 1/60 hours
