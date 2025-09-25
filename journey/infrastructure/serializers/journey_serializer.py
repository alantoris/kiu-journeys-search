"""
Journey Serializer - Django REST Framework serializers for API responses
"""
from rest_framework import serializers
from datetime import date

from ...core.entities.flight_event import FlightEvent


class FlightEventSerializer(serializers.Serializer):
    """
    Serializer for FlightEvent domain entity.
    Converts FlightEvent to the required API response format.
    """
    flight_number = serializers.CharField()
    from_field = serializers.CharField(source='from_city')  # 'from' is a Python keyword
    to = serializers.CharField(source='to_city')
    departure_time = serializers.SerializerMethodField()
    arrival_time = serializers.SerializerMethodField()
    
    def get_departure_time(self, obj: FlightEvent) -> str:
        """Format departure time as 'YYYY-MM-DD HH:MM'"""
        return obj.departure_time.strftime('%Y-%m-%d %H:%M')
    
    def get_arrival_time(self, obj: FlightEvent) -> str:
        """Format arrival time as 'YYYY-MM-DD HH:MM'"""
        return obj.arrival_time.strftime('%Y-%m-%d %H:%M')
    
    def to_representation(self, instance):
        """Override to use 'from' instead of 'from_field' in output"""
        ret = super().to_representation(instance)
        ret['from'] = ret.pop('from_field')
        return ret


class JourneySerializer(serializers.Serializer):
    """
    Serializer for Journey domain entity.
    Converts Journey to the required API response format.
    """
    connections = serializers.IntegerField()
    path = FlightEventSerializer(many=True)


class JourneySearchRequestSerializer(serializers.Serializer):
    """
    Serializer for validating journey search request parameters.
    """
    date = serializers.DateField(
        help_text="Search date in YYYY-MM-DD format"
    )
    from_param = serializers.CharField(
        source='from_city',
        max_length=3,
        min_length=3,
        help_text="Origin city code (3 letters)"
    )
    to = serializers.CharField(
        source='to_city',
        max_length=3,
        min_length=3,
        help_text="Destination city code (3 letters)"
    )
    
    def __init__(self, *args, **kwargs):
        # Handle 'from' parameter name (Python keyword)
        if 'data' in kwargs and isinstance(kwargs['data'], dict) and 'from' in kwargs['data']:
            data_copy = kwargs['data'].copy()
            data_copy['from_param'] = data_copy.pop('from')
            kwargs['data'] = data_copy
        super().__init__(*args, **kwargs)
    
    def validate(self, data):
        """Cross-field validation"""
        from_city = data.get('from_city', '').upper()
        to_city = data.get('to_city', '').upper()
        search_date = data.get('date')
        
        # Validate that origin and destination are different
        if from_city == to_city:
            raise serializers.ValidationError(
                "Origin and destination cities cannot be the same"
            )
        
        # Normalize city codes to uppercase
        data['from_city'] = from_city
        data['to_city'] = to_city
        
        return data
