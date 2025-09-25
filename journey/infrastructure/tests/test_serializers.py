"""
Tests for Journey Serializers
"""
from datetime import date
from freezegun import freeze_time

from ..serializers.journey_serializer import JourneySearchRequestSerializer


class TestJourneySearchRequestSerializer:
    """Test cases for JourneySearchRequestSerializer"""
    
    @freeze_time("2024-09-15")
    def test_valid_future_date(self):
        """Test that future dates are accepted"""
        data = {
            'date': '2024-09-16',
            'from': 'MAD',
            'to': 'BCN'
        }
        
        serializer = JourneySearchRequestSerializer(data=data)
        assert serializer.is_valid()
        
        validated_data = serializer.validated_data
        assert validated_data['date'] == date(2024, 9, 16)
        assert validated_data['from_city'] == 'MAD'
        assert validated_data['to_city'] == 'BCN'
    
    @freeze_time("2024-09-15")
    def test_valid_today_date(self):
        """Test that today's date is accepted"""
        data = {
            'date': '2024-09-15',
            'from': 'MAD',
            'to': 'BCN'
        }
        
        serializer = JourneySearchRequestSerializer(data=data)
        assert serializer.is_valid()
        
        validated_data = serializer.validated_data
        assert validated_data['date'] == date(2024, 9, 15)
    
    @freeze_time("2024-09-15")
    def test_past_date_is_valid(self):
        """Test that past dates are now accepted"""
        data = {
            'date': '2024-09-14',  # Yesterday
            'from': 'MAD',
            'to': 'BCN'
        }
        
        serializer = JourneySearchRequestSerializer(data=data)
        assert serializer.is_valid()
        
        validated_data = serializer.validated_data
        assert validated_data['date'] == date(2024, 9, 14)
    
    @freeze_time("2024-09-15")
    def test_far_past_date_is_valid(self):
        """Test that dates far in the past are now accepted"""
        data = {
            'date': '2024-01-01',  # Far in the past
            'from': 'MAD',
            'to': 'BCN'
        }
        
        serializer = JourneySearchRequestSerializer(data=data)
        assert serializer.is_valid()
        
        validated_data = serializer.validated_data
        assert validated_data['date'] == date(2024, 1, 1)
    
    def test_invalid_date_format(self):
        """Test that invalid date formats are rejected"""
        data = {
            'date': '2024/09/15',  # Wrong format
            'from': 'MAD',
            'to': 'BCN'
        }
        
        serializer = JourneySearchRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'date' in serializer.errors
    
    def test_same_origin_destination_error(self):
        """Test that same origin and destination is rejected"""
        data = {
            'date': '2024-12-15',
            'from': 'MAD',
            'to': 'MAD'  # Same as origin
        }
        
        serializer = JourneySearchRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Origin and destination cities cannot be the same' in str(serializer.errors)
    
    def test_missing_required_fields(self):
        """Test that missing required fields are rejected"""
        data = {
            'date': '2024-12-15'
            # Missing 'from' and 'to'
        }
        
        serializer = JourneySearchRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'from_param' in serializer.errors
        assert 'to' in serializer.errors
    
    def test_invalid_city_code_length(self):
        """Test that invalid city code lengths are rejected"""
        data = {
            'date': '2024-12-15',
            'from': 'MADRID',  # Too long
            'to': 'BC'         # Too short
        }
        
        serializer = JourneySearchRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'from_param' in serializer.errors
        assert 'to' in serializer.errors
    
    @freeze_time("2024-09-15")
    def test_city_codes_normalized_to_uppercase(self):
        """Test that city codes are normalized to uppercase"""
        data = {
            'date': '2024-12-15',  # Future date
            'from': 'mad',  # lowercase
            'to': 'bcn'     # lowercase
        }
        
        serializer = JourneySearchRequestSerializer(data=data)
        assert serializer.is_valid()
        
        validated_data = serializer.validated_data
        assert validated_data['from_city'] == 'MAD'
        assert validated_data['to_city'] == 'BCN'
    
    @freeze_time("2024-09-15")
    def test_yesterday_date_validation_error(self):
        """Test that yesterday's date is rejected"""
        data = {
            'date': '2024-09-14',  # Yesterday
            'from': 'MAD',
            'to': 'BCN'
        }
        
        serializer = JourneySearchRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert 'Search date cannot be in the past' in str(serializer.errors)
    
    @freeze_time("2024-09-15")
    def test_today_date_is_valid(self):
        """Test that today's date is accepted"""
        data = {
            'date': '2024-09-15',  # Today
            'from': 'MAD',
            'to': 'BCN'
        }
        
        serializer = JourneySearchRequestSerializer(data=data)
        assert serializer.is_valid()
        
        validated_data = serializer.validated_data
        assert validated_data['date'] == date(2024, 9, 15)
