from rest_framework import serializers
from core.serializers import RegionSummarySerializer
from .models import NDVIData, SoilMoistureData, WeatherData, DroughtRiskAssessment


class NDVIDataSerializer(serializers.ModelSerializer):
    """Serializer for NDVI data"""
    region = RegionSummarySerializer(read_only=True)
    region_id = serializers.IntegerField(write_only=True)
    vegetation_health_status = serializers.ReadOnlyField()
    
    class Meta:
        model = NDVIData
        fields = [
            'id', 'region', 'region_id', 'date', 'ndvi_value',
            'satellite_source', 'cloud_cover_percent', 'data_quality',
            'vegetation_health_status', 'created_at'
        ]
        read_only_fields = ['created_at']


class SoilMoistureDataSerializer(serializers.ModelSerializer):
    """Serializer for Soil Moisture data"""
    region = RegionSummarySerializer(read_only=True)
    region_id = serializers.IntegerField(write_only=True)
    moisture_status = serializers.ReadOnlyField()
    
    class Meta:
        model = SoilMoistureData
        fields = [
            'id', 'region', 'region_id', 'date', 'moisture_percent',
            'soil_depth_cm', 'data_source', 'temperature_celsius',
            'moisture_status', 'created_at'
        ]
        read_only_fields = ['created_at']


class WeatherDataSerializer(serializers.ModelSerializer):
    """Serializer for Weather data"""
    region = RegionSummarySerializer(read_only=True)
    region_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = WeatherData
        fields = [
            'id', 'region', 'region_id', 'date', 'temperature_max',
            'temperature_min', 'temperature_avg', 'precipitation_mm',
            'humidity_percent', 'wind_speed_kmh', 'evapotranspiration_mm',
            'data_source', 'created_at'
        ]
        read_only_fields = ['created_at']


class DroughtRiskAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Drought Risk Assessment"""
    region = RegionSummarySerializer(read_only=True)
    region_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = DroughtRiskAssessment
        fields = [
            'id', 'region', 'region_id', 'assessment_date', 'risk_score',
            'risk_level', 'ndvi_component_score', 'soil_moisture_component_score',
            'weather_component_score', 'predicted_risk_7_days', 'predicted_risk_30_days',
            'model_version', 'confidence_score', 'recommended_actions', 'created_at'
        ]
        read_only_fields = ['created_at', 'risk_level']


class RegionalDroughtSummarySerializer(serializers.Serializer):
    """Serializer for regional drought summary data"""
    region_id = serializers.IntegerField()
    region_name = serializers.CharField()
    current_risk_level = serializers.CharField()
    current_risk_score = serializers.FloatField()
    last_assessment_date = serializers.DateField()
    
    # Latest data points
    latest_ndvi = serializers.FloatField(allow_null=True)
    latest_soil_moisture = serializers.FloatField(allow_null=True)
    days_since_rain = serializers.IntegerField(allow_null=True)
    
    # Trends
    risk_trend = serializers.CharField()  # 'increasing', 'decreasing', 'stable'
    ndvi_trend = serializers.CharField()
    
    # Alert status
    active_alerts_count = serializers.IntegerField()


class DroughtTimeSeriesSerializer(serializers.Serializer):
    """Serializer for time series drought data"""
    date = serializers.DateField()
    risk_score = serializers.FloatField()
    ndvi_value = serializers.FloatField(allow_null=True)
    soil_moisture = serializers.FloatField(allow_null=True)
    precipitation = serializers.FloatField(allow_null=True)
    temperature_avg = serializers.FloatField(allow_null=True)


class DroughtComparisonSerializer(serializers.Serializer):
    """Serializer for comparing drought conditions across periods"""
    current_period = serializers.DictField()
    previous_period = serializers.DictField()
    historical_average = serializers.DictField()
    percentile_rank = serializers.FloatField(help_text="Current conditions percentile vs historical")


class DataAvailabilitySerializer(serializers.Serializer):
    """Serializer for data availability status"""
    region_id = serializers.IntegerField()
    region_name = serializers.CharField()
    
    # Data availability flags
    has_ndvi_data = serializers.BooleanField()
    has_soil_moisture_data = serializers.BooleanField()
    has_weather_data = serializers.BooleanField()
    has_risk_assessment = serializers.BooleanField()
    
    # Latest data dates
    latest_ndvi_date = serializers.DateField(allow_null=True)
    latest_soil_moisture_date = serializers.DateField(allow_null=True)
    latest_weather_date = serializers.DateField(allow_null=True)
    latest_assessment_date = serializers.DateField(allow_null=True)
    
    # Data quality scores
    ndvi_data_quality = serializers.CharField(allow_null=True)
    overall_data_completeness = serializers.FloatField()  # 0-1 score