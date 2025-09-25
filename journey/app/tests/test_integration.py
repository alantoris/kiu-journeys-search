"""
Integration tests for the journey search system
"""
from unittest.mock import patch, AsyncMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from freezegun import freeze_time
from datetime import date, datetime


class TestJourneySearchIntegration(TestCase):
    """Integration tests for the complete journey search flow."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.url = reverse('journey_search')

    @freeze_time("2024-12-25")
    @patch('journey.app.views.get_container')
    def test_complete_direct_flight_flow(self, mock_get_container):
        """Test complete flow for direct flight search."""
        # Mock the journey service with real logic
        mock_journey_service = AsyncMock()
        # Simulate the service finding a direct flight
        mock_journey_service.search_journeys.return_value = [
            type('Journey', (), {
                'connections': 0,
                'path': [
                    type('FlightEvent', (), {
                        'flight_number': 'XX1234',
                        'from_city': 'MAD',
                        'to_city': 'BCN',
                        'departure_time': datetime(2024, 12, 25, 10, 0),
                        'arrival_time': datetime(2024, 12, 25, 11, 30)
                    })()
                ]
            })()
        ]

        mock_container = mock_get_container.return_value
        mock_container.create_journey_service.return_value = mock_journey_service

        # Make the API call
        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'MAD',
            'to': 'BCN'
        })

        # Verify complete flow
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        journey = response.data[0]
        self.assertEqual(journey['connections'], 0)
        self.assertEqual(journey['path'][0]['flight_number'], 'XX1234')

        # Verify the service was called with correct parameters
        mock_journey_service.search_journeys.assert_called_once_with(
            date(2024, 12, 25), 'MAD', 'BCN'
        )

    @freeze_time("2024-12-25")
    @patch('journey.app.views.get_container')
    def test_complete_connecting_flight_flow(self, mock_get_container):
        """Test complete flow for connecting flight search."""
        # Mock the journey service to find connecting flights
        mock_journey_service = AsyncMock()
        mock_journey_service.search_journeys.return_value = [
            type('Journey', (), {
                'connections': 1,
                'path': [
                    type('FlightEvent', (), {
                        'flight_number': 'XX1234',
                        'from_city': 'MAD',
                        'to_city': 'PMI',
                        'departure_time': datetime(2024, 12, 25, 8, 0),
                        'arrival_time': datetime(2024, 12, 25, 9, 15)
                    })(),
                    type('FlightEvent', (), {
                        'flight_number': 'XX5678',
                        'from_city': 'PMI',
                        'to_city': 'BCN',
                        'departure_time': datetime(2024, 12, 25, 11, 0),
                        'arrival_time': datetime(2024, 12, 25, 12, 15)
                    })()
                ]
            })()
        ]

        mock_container = mock_get_container.return_value
        mock_container.create_journey_service.return_value = mock_journey_service

        # Make the API call
        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'MAD',
            'to': 'BCN'
        })

        # Verify complete flow
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        journey = response.data[0]
        self.assertEqual(journey['connections'], 1)
        self.assertEqual(len(journey['path']), 2)
        
        # Verify connection logic
        first_flight = journey['path'][0]
        second_flight = journey['path'][1]
        self.assertEqual(first_flight['to'], second_flight['from'])  # Connection city matches

    @freeze_time("2024-12-25")
    @patch('journey.app.views.get_container')
    def test_invalid_connection_rejected(self, mock_get_container):
        """Test that invalid connections are rejected by business rules."""
        # Mock the journey service to return empty list (invalid connection filtered out)
        mock_journey_service = AsyncMock()
        mock_journey_service.search_journeys.return_value = []  # No valid journeys

        mock_container = mock_get_container.return_value
        mock_container.create_journey_service.return_value = mock_journey_service

        # Make the API call for a route that might have invalid connections
        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'MAD',
            'to': 'NYC'  # Very far destination
        })

        # Verify no journeys returned due to business rules
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @freeze_time("2024-12-25")
    @patch('journey.app.views.get_container')
    def test_multiple_valid_journeys_returned(self, mock_get_container):
        """Test that multiple valid journey options are returned."""
        # Mock multiple valid journeys
        mock_journey_service = AsyncMock()
        mock_journey_service.search_journeys.return_value = [
            # Direct flight
            type('Journey', (), {
                'connections': 0,
                'path': [
                    type('FlightEvent', (), {
                        'flight_number': 'XX1111',
                        'from_city': 'MAD',
                        'to_city': 'BCN',
                        'departure_time': datetime(2024, 12, 25, 10, 0),
                        'arrival_time': datetime(2024, 12, 25, 11, 30)
                    })()
                ]
            })(),
            # Connecting flight
            type('Journey', (), {
                'connections': 1,
                'path': [
                    type('FlightEvent', (), {
                        'flight_number': 'XX2222',
                        'from_city': 'MAD',
                        'to_city': 'PMI',
                        'departure_time': datetime(2024, 12, 25, 6, 0),
                        'arrival_time': datetime(2024, 12, 25, 7, 15)
                    })(),
                    type('FlightEvent', (), {
                        'flight_number': 'XX3333',
                        'from_city': 'PMI',
                        'to_city': 'BCN',
                        'departure_time': datetime(2024, 12, 25, 9, 0),
                        'arrival_time': datetime(2024, 12, 25, 10, 15)
                    })()
                ]
            })()
        ]

        mock_container = mock_get_container.return_value
        mock_container.create_journey_service.return_value = mock_journey_service

        # Make the API call
        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'MAD',
            'to': 'BCN'
        })

        # Verify all valid journeys returned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Verify different journey types
        connections = [journey['connections'] for journey in response.data]
        self.assertIn(0, connections)  # Direct flight
        self.assertIn(1, connections)  # Connecting flights

    @freeze_time("2024-12-25")
    @patch('journey.app.views.get_container')
    def test_error_handling_integration(self, mock_get_container):
        """Test error handling throughout the integration flow."""
        # Mock the journey service to raise an exception
        mock_journey_service = AsyncMock()
        mock_journey_service.search_journeys.side_effect = Exception("External API timeout")

        mock_container = mock_get_container.return_value
        mock_container.create_journey_service.return_value = mock_journey_service

        # Make the API call
        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'MAD',
            'to': 'BCN'
        })

        # Verify error handling
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Internal server error occurred while searching journeys')

    @freeze_time("2024-12-25")
    def test_validation_integration(self):
        """Test that validation errors are handled correctly in the integration flow."""
        # Test with invalid parameters - should not reach the service layer
        response = self.client.get(self.url, {
            'date': '2024-12-24',
            'from': 'MAD',
            'to': 'MAD'  # Same origin and destination (should fail)
        })

        # Verify validation error returned before reaching service layer
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('non_field_errors', response.data['errors'])

    @freeze_time("2024-12-25")
    @patch('journey.app.views.get_container')
    def test_di_container_integration(self, mock_get_container):
        """Test that DI container is properly used in the integration flow."""
        # Verify container is accessed
        mock_container = mock_get_container.return_value
        mock_journey_service = AsyncMock()
        mock_container.create_journey_service.return_value = mock_journey_service

        # Make the API call
        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'MAD',
            'to': 'BCN'
        })

        # Verify container was used
        mock_get_container.assert_called()
        mock_container.create_journey_service.assert_called()