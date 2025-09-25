"""
Journey API Views - Application layer entry points
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import asyncio
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..di import get_container
from ..infrastructure.serializers.journey_serializer import (
    JourneySearchRequestSerializer,
    JourneySerializer
)

logger = logging.getLogger(__name__)


class JourneySearchView(APIView):
    """
    API endpoint for journey search.
    GET /journey/search?date=YYYY-MM-DD&from=XXX&to=YYY
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Dependency injection using our DI container
        self.container = get_container()
        self.journey_service = self.container.create_journey_service()
    
    @swagger_auto_schema(
        operation_id='search_journeys',
        operation_summary='Search Flight Journeys',
        operation_description="""
        Search for flight journeys between two cities on a specific date.
        
        Returns both direct flights (0 connections) and connecting flights (1 connection).
        
        **Business Rules:**
        - Maximum 2 flights per journey (v1.0 limitation)
        - Origin and destination must be different
        - Connection time between flights: max 4 hours
        - Total journey duration: max 24 hours
        """,
        manual_parameters=[
            openapi.Parameter(
                'date',
                openapi.IN_QUERY,
                description='Search date in YYYY-MM-DD format',
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=True,
                example='2024-12-25'
            ),
            openapi.Parameter(
                'from',
                openapi.IN_QUERY,
                description='Origin city code (3 letters)',
                type=openapi.TYPE_STRING,
                required=True,
                example='MAD',
                pattern='^[A-Z]{3}$'
            ),
            openapi.Parameter(
                'to',
                openapi.IN_QUERY,
                description='Destination city code (3 letters)',
                type=openapi.TYPE_STRING,
                required=True,
                example='BCN',
                pattern='^[A-Z]{3}$'
            ),
        ],
        responses={
            200: openapi.Response(
                description='List of available journeys',
                examples={
                    'application/json': [
                        {
                            "connections": 0,
                            "path": [
                                {
                                    "flight_number": "XX1234",
                                    "from": "MAD",
                                    "to": "BCN", 
                                    "departure_time": "2024-12-25 10:00",
                                    "arrival_time": "2024-12-25 11:30"
                                }
                            ]
                        }
                    ]
                }
            ),
            400: openapi.Response(
                description='Validation errors',
                examples={
                    'application/json': {
                        "errors": {
                            "date": ["Date has wrong format. Use YYYY-MM-DD."],
                            "non_field_errors": ["Origin and destination cities cannot be the same"]
                        }
                    }
                }
            ),
            500: openapi.Response(
                description='Internal server error',
                examples={
                    'application/json': {
                        "error": "Internal server error",
                        "message": "Unable to fetch flight data"
                    }
                }
            )
        },
        tags=['Journey Search']
    )
    def get(self, request):
        """Search for flight journeys between two cities on a specific date."""
        # Extract query parameters explicitly
        query_params = {
            'date': request.query_params.get('date'),
            'from': request.query_params.get('from'),
            'to': request.query_params.get('to')
        }
        
        # Validate request parameters
        serializer = JourneySearchRequestSerializer(data=query_params)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract validated data
        validated_data = serializer.validated_data
        search_date = validated_data['date']
        from_city = validated_data['from_city']
        to_city = validated_data['to_city']
        
        try:
            # Call the domain service (async operation)
            journeys = asyncio.run(
                self.journey_service.search_journeys(search_date, from_city, to_city)
            )
            
            # Serialize the response
            journey_serializer = JourneySerializer(journeys, many=True)
            
            return Response(journey_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error searching journeys: {str(e)}")
            return Response(
                {"error": "Internal server error occurred while searching journeys"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
