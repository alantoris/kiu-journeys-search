"""
Tests for API endpoints
"""
from unittest.mock import patch, AsyncMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from freezegun import freeze_time
from datetime import datetime


class TestJourneySearchAPI(TestCase):
    """Tests for the Journey Search API endpoint."""

    def setUp(self):
        """Set up test client and mock data."""
        self.client = APIClient()
        self.url = reverse('journey_search')

    @freeze_time("2024-12-25")
    @patch('journey.app.views.get_container')
    def test_successful_direct_flight_search(self, mock_get_container):
        """Test successful search returning direct flights."""
        # Mock the journey service to return direct flights
        mock_journey_service = AsyncMock()
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

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        
        journey = response.data[0]
        self.assertEqual(journey['connections'], 0)
        self.assertEqual(len(journey['path']), 1)
        
        flight = journey['path'][0]
        self.assertEqual(flight['flight_number'], 'XX1234')
        self.assertEqual(flight['from'], 'MAD')
        self.assertEqual(flight['to'], 'BCN')
        self.assertEqual(flight['departure_time'], '2024-12-25 10:00')
        self.assertEqual(flight['arrival_time'], '2024-12-25 11:30')

    @freeze_time("2024-12-25")
    @patch('journey.app.views.get_container')
    def test_successful_connecting_flight_search(self, mock_get_container):
        """Test successful search returning connecting flights."""
        # Mock the journey service to return connecting flights
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

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        journey = response.data[0]
        self.assertEqual(journey['connections'], 1)
        self.assertEqual(len(journey['path']), 2)
        
        # Check first flight
        first_flight = journey['path'][0]
        self.assertEqual(first_flight['flight_number'], 'XX1234')
        self.assertEqual(first_flight['from'], 'MAD')
        self.assertEqual(first_flight['to'], 'PMI')
        
        # Check second flight
        second_flight = journey['path'][1]
        self.assertEqual(second_flight['flight_number'], 'XX5678')
        self.assertEqual(second_flight['from'], 'PMI')
        self.assertEqual(second_flight['to'], 'BCN')

    @freeze_time("2024-12-25")
    def test_missing_required_parameters(self):
        """Test API call with missing required parameters."""
        # Missing 'to' parameter
        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'MAD'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('to', response.data['errors'])

    @freeze_time("2024-12-25")
    def test_invalid_date_format(self):
        """Test API call with invalid date format."""
        response = self.client.get(self.url, {
            'date': '2024/12/25',  # Invalid format
            'from': 'MAD',
            'to': 'BCN'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('date', response.data['errors'])

    @freeze_time("2024-12-25")
    def test_past_date_validation(self):
        """Test API call with past date."""
        response = self.client.get(self.url, {
            'date': '2024-12-24',  # Past date
            'from': 'MAD',
            'to': 'BCN'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('non_field_errors', response.data['errors'])
        self.assertIn('Search date cannot be in the past', str(response.data['errors']))

    @freeze_time("2024-12-25")
    def test_same_origin_destination(self):
        """Test API call with same origin and destination."""
        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'MAD',
            'to': 'MAD'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('non_field_errors', response.data['errors'])
        self.assertIn('Origin and destination cities cannot be the same', str(response.data['errors']))

    @freeze_time("2024-12-25")
    @patch('journey.app.views.get_container')
    def test_no_journeys_found(self, mock_get_container):
        """Test API call when no journeys are found."""
        # Mock the journey service to return empty list
        mock_journey_service = AsyncMock()
        mock_journey_service.search_journeys.return_value = []
        
        mock_container = mock_get_container.return_value
        mock_container.create_journey_service.return_value = mock_journey_service

        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'MAD',
            'to': 'BCN'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @freeze_time("2024-12-25")
    @patch('journey.app.views.get_container')
    def test_external_api_error(self, mock_get_container):
        """Test API call when external API fails."""
        # Mock the journey service to raise an exception
        mock_journey_service = AsyncMock()
        mock_journey_service.search_journeys.side_effect = Exception("External API error")
        
        mock_container = mock_get_container.return_value
        mock_container.create_journey_service.return_value = mock_journey_service

        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'MAD',
            'to': 'BCN'
        })

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Internal server error occurred while searching journeys')

    @freeze_time("2024-12-25")
    def test_case_insensitive_city_codes(self):
        """Test that city codes are case insensitive."""
        # This test would require mocking the serializer to verify normalization
        # For now, we'll test the endpoint accepts lowercase codes
        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'mad',  # lowercase
            'to': 'bcn'     # lowercase
        })

        # Should not return a validation error for case
        # (The actual normalization is tested in serializer tests)
        self.assertNotEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @freeze_time("2024-12-25")
    @patch('journey.app.views.get_container')
    def test_multiple_journeys_returned(self, mock_get_container):
        """Test API call returning multiple journey options."""
        # Mock multiple journeys (direct + connecting)
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
                        'departure_time': datetime(2024, 12, 25, 8, 0),
                        'arrival_time': datetime(2024, 12, 25, 9, 15)
                    })(),
                    type('FlightEvent', (), {
                        'flight_number': 'XX3333',
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

        response = self.client.get(self.url, {
            'date': '2024-12-25',
            'from': 'MAD',
            'to': 'BCN'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # First journey should be direct
        self.assertEqual(response.data[0]['connections'], 0)
        self.assertEqual(len(response.data[0]['path']), 1)
        
        # Second journey should be connecting
        self.assertEqual(response.data[1]['connections'], 1)
        self.assertEqual(len(response.data[1]['path']), 2)
