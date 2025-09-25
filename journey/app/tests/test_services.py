"""
Tests for domain services
"""
import pytest
from unittest.mock import AsyncMock
from datetime import date, datetime
from django.test import TestCase

from ...core.services.journey_service import JourneyService
from ...core.entities.flight_event import FlightEvent


class TestJourneyService(TestCase):
    """Tests for the JourneyService domain service."""

    def setUp(self):
        """Set up test data."""
        self.flight_events_port = AsyncMock()
        self.journey_service = JourneyService(flight_events_port=self.flight_events_port)

    @pytest.mark.asyncio
    async def test_search_direct_flights(self):
        """Test searching for direct flights."""
        # Mock flight events from external API
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
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify results
        self.assertEqual(len(journeys), 1)
        journey = journeys[0]
        self.assertEqual(journey.connections, 0)
        self.assertEqual(len(journey.path), 1)
        self.assertEqual(journey.path[0].flight_number, "XX1234")

    @pytest.mark.asyncio
    async def test_search_connecting_flights(self):
        """Test searching for connecting flights."""
        # Mock flight events that can be connected
        mock_flight_events = [
            # MAD -> PMI
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 8, 0),
                arrival_time=datetime(2024, 12, 25, 9, 15)
            ),
            # PMI -> BCN
            FlightEvent(
                flight_number="XX5678",
                from_city="PMI",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 11, 0),
                arrival_time=datetime(2024, 12, 25, 12, 15)
            ),
            # MAD -> BCN (direct)
            FlightEvent(
                flight_number="XX9999",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 25, 11, 30)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify results - should find both direct and connecting
        self.assertEqual(len(journeys), 2)
        
        # Find direct flight
        direct_journey = next(j for j in journeys if j.connections == 0)
        self.assertEqual(direct_journey.path[0].flight_number, "XX9999")
        
        # Find connecting flight
        connecting_journey = next(j for j in journeys if j.connections == 1)
        self.assertEqual(len(connecting_journey.path), 2)
        self.assertEqual(connecting_journey.path[0].flight_number, "XX1234")
        self.assertEqual(connecting_journey.path[1].flight_number, "XX5678")

    @pytest.mark.asyncio
    async def test_invalid_connection_filtered_out(self):
        """Test that invalid connections are filtered out."""
        # Mock flight events with invalid connection
        mock_flight_events = [
            # MAD -> PMI
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 8, 0),
                arrival_time=datetime(2024, 12, 25, 9, 15)
            ),
            # PMI -> BCN (but connection time too long - 6 hours)
            FlightEvent(
                flight_number="XX5678",
                from_city="PMI",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 15, 0),  # 6 hours later
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
    async def test_no_flights_found(self):
        """Test when no flights are found for the route."""
        # Mock empty flight events
        self.flight_events_port.get_flight_events.return_value = []

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="NYC"  # Very far destination
        )

        # Verify no journeys returned
        self.assertEqual(len(journeys), 0)

    @pytest.mark.asyncio
    async def test_external_api_error_handling(self):
        """Test handling of external API errors."""
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
    async def test_journey_duration_limit(self):
        """Test that journeys exceeding duration limit are filtered out."""
        # Mock flight events with journey exceeding 24 hours
        mock_flight_events = [
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 10, 0),
                arrival_time=datetime(2024, 12, 26, 11, 0)  # 25 hours later
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify no journeys returned due to duration limit
        self.assertEqual(len(journeys), 0)

    @pytest.mark.asyncio
    async def test_connection_time_validation(self):
        """Test connection time validation between flights."""
        # Mock flight events with valid connection time (3 hours)
        mock_flight_events = [
            FlightEvent(
                flight_number="XX1234",
                from_city="MAD",
                to_city="PMI",
                departure_time=datetime(2024, 12, 25, 8, 0),
                arrival_time=datetime(2024, 12, 25, 9, 15)
            ),
            FlightEvent(
                flight_number="XX5678",
                from_city="PMI",
                to_city="BCN",
                departure_time=datetime(2024, 12, 25, 12, 15),  # 3 hours connection
                arrival_time=datetime(2024, 12, 25, 13, 30)
            )
        ]
        
        self.flight_events_port.get_flight_events.return_value = mock_flight_events

        # Search for journeys
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify valid connection is found
        self.assertEqual(len(journeys), 1)
        journey = journeys[0]
        self.assertEqual(journey.connections, 1)
        self.assertEqual(len(journey.path), 2)

    @pytest.mark.asyncio
    async def test_multiple_valid_connections(self):
        """Test finding multiple valid connection options."""
        # Mock flight events with multiple valid connections
        mock_flight_events = [
            # First connection option: MAD -> PMI -> BCN
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
            # Second connection option: MAD -> VAL -> BCN
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

        # Verify multiple connections found
        self.assertEqual(len(journeys), 2)
        
        # Both should be connecting flights
        for journey in journeys:
            self.assertEqual(journey.connections, 1)
            self.assertEqual(len(journey.path), 2)

    @pytest.mark.asyncio
    async def test_service_calls_external_port(self):
        """Test that the service properly calls the external port."""
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
    async def test_journey_entity_creation(self):
        """Test that Journey entities are properly created."""
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
        journeys = await self.journey_service.search_journeys(
            search_date=date(2024, 12, 25),
            from_city="MAD",
            to_city="BCN"
        )

        # Verify Journey entities are created correctly
        self.assertEqual(len(journeys), 1)
        journey = journeys[0]
        self.assertIsInstance(journey, Journey)
        self.assertEqual(journey.connections, 0)
        self.assertEqual(len(journey.path), 1)
        self.assertIsInstance(journey.path[0], FlightEvent)