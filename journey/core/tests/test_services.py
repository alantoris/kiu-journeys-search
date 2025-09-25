"""
Tests for domain services
"""
import pytest
from unittest.mock import AsyncMock
from datetime import date, datetime
from django.test import TestCase

from ..services.journey_service import JourneyService
from ..entities.flight_event import FlightEvent
from ..interfaces import FlightEventsPort


class TestJourneyService(TestCase):
    """Tests for JourneyService domain service."""

    def setUp(self):
        """Set up test data."""
        self.flight_events_port = AsyncMock(spec=FlightEventsPort)
        self.journey_service = JourneyService(flight_events_port=self.flight_events_port)

    @pytest.mark.asyncio
    async def test_search_direct_flights_only(self):
        """Test searching for direct flights only."""
        # Mock flight events
        mock_flight_events = [
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            ),
            FlightEvent(
                flight_number="XX5678",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 14, 0),
                arrival_time=datetime(2024, 12, 25, 15, 30)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify results
        self.assertEqual(len(journeys), 2)
        self.assertEqual(journeys[0].connections, 0)
        self.assertEqual(journeys[1].connections, 0)
        
        # Verify sorting by departure time
        self.assertEqual(journeys[0].path[0].flight_number, "XX1234")
        self.assertEqual(journeys[1].path[0].flight_number, "XX5678")

    @pytest.mark.asyncio
    async def test_search_connecting_flights_only(self):
        """Test searching for connecting flights only."""
        # Mock flight events that can be connected
        mock_flight_events = [
            # First leg: MAD -> PMI
            FlightEvent(
                flight_number="XX1111",
                from_city="MAD",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 8, 0),
                arrival_time=datetime(2024, 12, 25, 9, 15)
            ),
            # Second leg: PMI -> BCN
            FlightEvent(
                flight_number="XX2222",
                from_city="PMI",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 11, 0),
                arrival_time=datetime(2024, 12, 25, 12, 15)
            ),
            # Another first leg: MAD -> VAL
            FlightEvent(
                flight_number="XX3333",
                from_city="MAD",
                to_city="VAL",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 15)
            ),
            # Another second leg: VAL -> BCN
            FlightEvent(
                flight_number="XX4444",
                from_city="VAL",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 13, 0),
                arrival_time=datetime(2024, 12, 25, 14, 15)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify results
        self.assertEqual(len(journeys), 2)
        for journey in journeys:
            self.assertEqual(journey.connections, 1)
            self.assertEqual(journey.origin, "MAD")
            self.assertEqual(journey.destination, "BCN")

    @pytest.mark.asyncio
    async def test_search_mixed_direct_and_connecting_flights(self):
        """Test searching with both direct and connecting flights."""
        # Mock flight events with both types
        mock_flight_events = [
            # Direct flight
            FlightEvent(
                flight_number="XX1111",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            ),
            # Connecting flights
            FlightEvent(
                flight_number="XX2222",
                from_city="MAD",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 8, 0),
                arrival_time=datetime(2024, 12, 25, 9, 15)
            ),
            FlightEvent(
                flight_number="XX3333",
                from_city="PMI",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 11, 0),
                arrival_time=datetime(2024, 12, 25, 12, 15)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify results
        self.assertEqual(len(journeys), 2)
        
        # First journey should be direct (earlier departure)
        self.assertEqual(journeys[0].connections, 1)  # Connecting flight departs earlier
        self.assertEqual(journeys[1].connections, 0)  # Direct flight

    @pytest.mark.asyncio
    async def test_no_journeys_found(self):
        """Test when no journeys are found."""
        # Mock empty flight events
        self.flight_events_port.get_flight_events.return_value = []

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify no journeys returned
        self.assertEqual(len(journeys), 0)

    @pytest.mark.asyncio
    async def test_no_matching_flights(self):
        """Test when flights exist but none match the route."""
        # Mock flight events for different routes
        mock_flight_events = [
            FlightEvent(
                flight_number="XX1234",
                from_city="NYC",
                to_city="LAX",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 13, 0)
            ),
            FlightEvent(
                flight_number="XX5678",
                from_city="LON",
                to_city="PAR",
                departure_time=datetime(2024, 12, 25, 14, 0),
                arrival_time=datetime(2024, 12, 25, 15, 30)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify no journeys returned
        self.assertEqual(len(journeys), 0)

    @pytest.mark.asyncio
    async def test_invalid_connections_filtered_out(self):
        """Test that invalid connections are filtered out."""
        # Mock flight events with invalid connections
        mock_flight_events = [
            # First leg: MAD -> PMI
            FlightEvent(
                flight_number="XX1111",
                from_city="MAD",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 8, 0),
                arrival_time=datetime(2024, 12, 25, 9, 15)
            ),
            # Second leg: PMI -> BCN (but connection time too long - 6 hours)
            FlightEvent(
                flight_number="XX2222",
                from_city="PMI",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 15, 0),  # 6 hours after first flight
                arrival_time=datetime(2024, 12, 25, 16, 15)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify no journeys returned due to invalid connection
        self.assertEqual(len(journeys), 0)

    @pytest.mark.asyncio
    async def test_external_api_error_propagated(self):
        """Test that external API errors are propagated."""
        # Mock external API error
        self.flight_events_port.get_flight_events.side_effect = Exception("API timeout")

        # Search for journeys should raise the exception
        with self.assertRaises(Exception) as context:
            await self.journey_service.search_journeys(
                search_date=date(2024, 12, 25),
                from_city="MAD",
                to_city="BCN"
            )

        self.assertEqual(str(context.exception), "API timeout")

    @pytest.mark.asyncio
    async def test_service_calls_external_port_with_correct_date(self):
        """Test that service calls external port with correct date."""
        # Mock flight events
        mock_flight_events = [
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify external port was called with correct date
        self.flight_events_port.get_flight_events.assert_called_once_with(date(2024, 12, 25))

    @pytest.mark.asyncio
    async def test_multiple_connecting_options(self):
        """Test finding multiple connecting flight options."""
        # Mock flight events with multiple connection options
        mock_flight_events = [
            # Option 1: MAD -> PMI -> BCN
            FlightEvent(
                flight_number="XX1111",
                from_city="MAD",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 8, 0),
                arrival_time=datetime(2024, 12, 25, 9, 15)
            ),
            FlightEvent(
                flight_number="XX2222",
                from_city="PMI",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 11, 0),
                arrival_time=datetime(2024, 12, 25, 12, 15)
            ),
            # Option 2: MAD -> VAL -> BCN
            FlightEvent(
                flight_number="XX3333",
                from_city="MAD",
                to_city="VAL",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 15)
            ),
            FlightEvent(
                flight_number="XX4444",
                from_city="VAL",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 13, 0),
                arrival_time=datetime(2024, 12, 25, 14, 15)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify multiple connecting options found
        self.assertEqual(len(journeys), 2)
        
        # Both should be connecting flights
        for journey in journeys:
            self.assertEqual(journey.connections, 1)
            self.assertEqual(journey.origin, "MAD")
            self.assertEqual(journey.destination, "BCN")

    @pytest.mark.asyncio
    async def test_avoid_direct_flights_in_connecting_search(self):
        """Test that connecting search doesn't include direct flights."""
        # Mock flight events including a direct flight
        mock_flight_events = [
            # Direct flight MAD -> BCN
            FlightEvent(
                flight_number="XX1111",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            ),
            # Connecting flights MAD -> PMI -> BCN
            FlightEvent(
                flight_number="XX2222",
                from_city="MAD",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 8, 0),
                arrival_time=datetime(2024, 12, 25, 9, 15)
            ),
            FlightEvent(
                flight_number="XX3333",
                from_city="PMI",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 11, 0),
                arrival_time=datetime(2024, 12, 25, 12, 15)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify both direct and connecting flights found
        self.assertEqual(len(journeys), 2)
        
        # One direct, one connecting
        connections = [journey.connections for journey in journeys]
        self.assertIn(0, connections)  # Direct flight
        self.assertIn(1, connections)  # Connecting flight

    @pytest.mark.asyncio
    async def test_journey_sorting_by_departure_time(self):
        """Test that journeys are sorted by departure time."""
        # Mock flight events with different departure times
        mock_flight_events = [
            # Later direct flight
            FlightEvent(
                flight_number="XX1111",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 14, 0),
                arrival_time=datetime(2024, 12, 25, 15, 30)
            ),
            # Earlier connecting flight
            FlightEvent(
                flight_number="XX2222",
                from_city="MAD",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 8, 0),
                arrival_time=datetime(2024, 12, 25, 9, 15)
            ),
            FlightEvent(
                flight_number="XX3333",
                from_city="PMI",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 11, 0),
                arrival_time=datetime(2024, 12, 25, 12, 15)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify sorting by departure time
        self.assertEqual(len(journeys), 2)
        
        # First journey should be connecting (departs at 8:00)
        self.assertEqual(journeys[0].connections, 1)
        self.assertEqual(journeys[0].departure_time, datetime(2024, 12, 25, 8, 0))
        
        # Second journey should be direct (departs at 14:00)
        self.assertEqual(journeys[1].connections, 0)
        self.assertEqual(journeys[1].departure_time, datetime(2024, 12, 25, 14, 0))

    @pytest.mark.asyncio
    async def test_case_sensitive_city_matching(self):
        """Test that city matching is case sensitive."""
        # Mock flight events with different case
        mock_flight_events = [
            FlightEvent(
                flight_number="XX1234",
                from_city="mad",  # lowercase
                to_city="bcn",    # lowercase
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys with uppercase
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",  # uppercase
            to_city="BCN"     # uppercase
        )

        # Verify no journeys found due to case mismatch
        self.assertEqual(len(journeys), 0)

    @pytest.mark.asyncio
    async def test_journey_validation_errors_handled(self):
        """Test that journey validation errors are handled gracefully."""
        # Mock flight events that would create invalid journeys
        mock_flight_events = [
            # Flight with invalid duration (> 24 hours)
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 26, 11, 0)  # 25 hours
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify no journeys returned due to validation error
        self.assertEqual(len(journeys), 0)

    @pytest.mark.asyncio
    async def test_complex_route_with_multiple_connections(self):
        """Test complex route with multiple connection possibilities."""
        # Mock flight events for complex routing
        mock_flight_events = [
            # Direct flight
            FlightEvent(
                flight_number="XX1111",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 12, 0),
                arrival_time=datetime(2024, 12, 25, 13, 30)
            ),
            # Connection 1: MAD -> PMI -> BCN
            FlightEvent(
                flight_number="XX2222",
                from_city="MAD",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 8, 0),
                arrival_time=datetime(2024, 12, 25, 9, 15)
            ),
            FlightEvent(
                flight_number="XX3333",
                from_city="PMI",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 11, 0),
                arrival_time=datetime(2024, 12, 25, 12, 15)
            ),
            # Connection 2: MAD -> VAL -> BCN
            FlightEvent(
                flight_number="XX4444",
                from_city="MAD",
                to_city="VAL",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 15)
            ),
            FlightEvent(
                flight_number="XX5555",
                from_city="VAL",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 13, 0),
                arrival_time=datetime(2024, 12, 25, 14, 15)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify all valid journeys found
        self.assertEqual(len(journeys), 3)  # 1 direct + 2 connecting
        
        # Verify sorting by departure time
        departure_times = [journey.departure_time for journey in journeys]
        self.assertEqual(departure_times, sorted(departure_times))
        
        # Verify journey types
        connections = [journey.connections for journey in journeys]
        self.assertEqual(connections.count(0), 1)  # 1 direct
        self.assertEqual(connections.count(1), 2)  # 2 connecting
