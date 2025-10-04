from rest_framework import serializers
from core.serializers import UserProfileSerializer, RegionSummarySerializer
from .models import FarmerProfile, FarmField, CropCalendar, FarmerGroup


class FarmerProfileSerializer(serializers.ModelSerializer):
    """Serializer for FarmerProfile model"""
    user_profile = UserProfileSerializer(read_only=True)
    user_profile_id = serializers.IntegerField(write_only=True)
    crops_list = serializers.ReadOnlyField()
    
    class Meta:
        model = FarmerProfile
        fields = [
            'id', 'user_profile', 'user_profile_id', 'farm_name', 'farming_type',
            'irrigation_type', 'main_crops', 'crops_list', 'livestock_count',
            'farm_latitude', 'farm_longitude', 'annual_income_bracket',
            'years_farming', 'has_smartphone', 'uses_weather_apps',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class FarmFieldSerializer(serializers.ModelSerializer):
    """Serializer for FarmField model"""
    farmer = FarmerProfileSerializer(read_only=True)
    farmer_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = FarmField
        fields = [
            'id', 'farmer', 'farmer_id', 'field_name', 'latitude', 'longitude',
            'area_acres', 'soil_type', 'current_crop', 'planting_date',
            'expected_harvest_date', 'is_active', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class FarmFieldSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for FarmField listings"""
    class Meta:
        model = FarmField
        fields = ['id', 'field_name', 'area_acres', 'current_crop', 'is_active']


class CropCalendarSerializer(serializers.ModelSerializer):
    """Serializer for CropCalendar model"""
    region = RegionSummarySerializer(read_only=True)
    region_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CropCalendar
        fields = [
            'id', 'crop_name', 'region', 'region_id', 'optimal_planting_start',
            'optimal_planting_end', 'growing_days_min', 'growing_days_max',
            'water_requirement_mm', 'critical_stages', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class FarmerGroupSerializer(serializers.ModelSerializer):
    """Serializer for FarmerGroup model"""
    region = RegionSummarySerializer(read_only=True)
    region_id = serializers.IntegerField(write_only=True)
    chairman = FarmerProfileSerializer(read_only=True)
    chairman_id = serializers.IntegerField(write_only=True, required=False)
    member_count = serializers.ReadOnlyField()
    
    class Meta:
        model = FarmerGroup
        fields = [
            'id', 'name', 'description', 'region', 'region_id', 'chairman',
            'chairman_id', 'member_count', 'registration_number', 'formation_date',
            'contact_phone', 'contact_email', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class FarmerGroupMembershipSerializer(serializers.Serializer):
    """Serializer for managing farmer group memberships"""
    farmer_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['add', 'remove'])


class FarmerStatsSerializer(serializers.Serializer):
    """Serializer for farmer statistics"""
    total_farmers = serializers.IntegerField()
    active_farmers = serializers.IntegerField()
    
    # By farming type
    farming_type_distribution = serializers.DictField()
    
    # By irrigation type
    irrigation_type_distribution = serializers.DictField()
    
    # By region
    regional_distribution = serializers.DictField()
    
    # Technology adoption
    smartphone_adoption_rate = serializers.FloatField()
    weather_app_usage_rate = serializers.FloatField()
    
    # Farm sizes
    average_farm_size = serializers.FloatField()
    total_cultivated_area = serializers.FloatField()
    
    # Groups
    total_farmer_groups = serializers.IntegerField()
    farmers_in_groups = serializers.IntegerField()


class FarmerDashboardSerializer(serializers.Serializer):
    """Serializer for farmer dashboard data"""
    farmer_profile = FarmerProfileSerializer()
    
    # Farm overview
    total_fields = serializers.IntegerField()
    total_area = serializers.FloatField()
    active_crops = serializers.ListField(child=serializers.CharField())
    
    # Current season info
    current_planting_season = serializers.DictField(allow_null=True)
    upcoming_harvests = serializers.ListField(child=serializers.DictField())
    
    # Risk information
    current_drought_risk = serializers.DictField(allow_null=True)
    recent_alerts = serializers.ListField(child=serializers.DictField())
    
    # Weather summary
    weather_summary = serializers.DictField(allow_null=True)
    
    # Recommendations
    recommendations = serializers.ListField(child=serializers.CharField())


class PlantingAdvisorySerializer(serializers.Serializer):
    """Serializer for planting advisory information"""
    crop_name = serializers.CharField()
    region_name = serializers.CharField()
    
    # Current status
    is_optimal_planting_window = serializers.BooleanField()
    days_until_optimal_start = serializers.IntegerField(allow_null=True)
    days_until_optimal_end = serializers.IntegerField(allow_null=True)
    
    # Conditions
    current_soil_moisture = serializers.FloatField(allow_null=True)
    recent_rainfall = serializers.FloatField(allow_null=True)
    weather_forecast = serializers.DictField()
    
    # Risk assessment
    drought_risk_level = serializers.CharField()
    planting_risk_score = serializers.FloatField()
    
    # Recommendations
    recommendation = serializers.CharField()
    alternative_crops = serializers.ListField(child=serializers.CharField())
    irrigation_advice = serializers.CharField()