from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Max, Min, Count, Sum
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
import statistics

from .models import NDVIData, SoilMoistureData, WeatherData, DroughtRiskAssessment
from .serializers import (
    NDVIDataSerializer, SoilMoistureDataSerializer, WeatherDataSerializer,
    DroughtRiskAssessmentSerializer, RegionalDroughtSummarySerializer,
    DroughtTimeSeriesSerializer, DroughtComparisonSerializer,
    DataAvailabilitySerializer
)
from core.models import Region


class NDVIDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for NDVI data management
    """
    queryset = NDVIData.objects.all()
    serializer_class = NDVIDataSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['region', 'date', 'satellite_source', 'data_quality']
    ordering_fields = ['date', 'ndvi_value']
    ordering = ['-date', 'region']
    
    @action(detail=False, methods=['get'])
    def latest_by_region(self, request):
        """Get latest NDVI data for each region"""
        region_id = request.query_params.get('region')
        
        if region_id:
            try:
                latest = NDVIData.objects.filter(region_id=region_id).order_by('-date').first()
                if latest:
                    serializer = self.get_serializer(latest)
                    return Response(serializer.data)
                return Response({'message': 'No NDVI data found for this region'})
            except:
                return Response({'error': 'Invalid region ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get latest for all regions
        latest_data = []
        regions = Region.objects.all()
        
        for region in regions:
            latest = NDVIData.objects.filter(region=region).order_by('-date').first()
            if latest:
                latest_data.append(latest)
        
        serializer = self.get_serializer(latest_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def time_series(self, request):
        """Get NDVI time series for a region"""
        region_id = request.query_params.get('region')
        days = int(request.query_params.get('days', 90))
        
        if not region_id:
            return Response({'error': 'region parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        data = NDVIData.objects.filter(
            region_id=region_id,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get NDVI statistics for a region"""
        region_id = request.query_params.get('region')
        days = int(request.query_params.get('days', 30))
        
        if not region_id:
            return Response({'error': 'region parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        stats = NDVIData.objects.filter(
            region_id=region_id,
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(
            avg_ndvi=Avg('ndvi_value'),
            max_ndvi=Max('ndvi_value'),
            min_ndvi=Min('ndvi_value'),
            count=Count('id')
        )
        
        return Response(stats)


class SoilMoistureDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Soil Moisture data management
    """
    queryset = SoilMoistureData.objects.all()
    serializer_class = SoilMoistureDataSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['region', 'date', 'data_source', 'soil_depth_cm']
    ordering_fields = ['date', 'moisture_percent']
    ordering = ['-date', 'region']
    
    @action(detail=False, methods=['get'])
    def latest_by_region(self, request):
        """Get latest soil moisture data for each region"""
        region_id = request.query_params.get('region')
        
        if region_id:
            try:
                latest = SoilMoistureData.objects.filter(region_id=region_id).order_by('-date').first()
                if latest:
                    serializer = self.get_serializer(latest)
                    return Response(serializer.data)
                return Response({'message': 'No soil moisture data found for this region'})
            except:
                return Response({'error': 'Invalid region ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get latest for all regions
        latest_data = []
        regions = Region.objects.all()
        
        for region in regions:
            latest = SoilMoistureData.objects.filter(region=region).order_by('-date').first()
            if latest:
                latest_data.append(latest)
        
        serializer = self.get_serializer(latest_data, many=True)
        return Response(serializer.data)


class WeatherDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Weather data management
    """
    queryset = WeatherData.objects.all()
    serializer_class = WeatherDataSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['region', 'date', 'data_source']
    ordering_fields = ['date', 'temperature_avg', 'precipitation_mm']
    ordering = ['-date', 'region']
    
    @action(detail=False, methods=['get'])
    def rainfall_summary(self, request):
        """Get rainfall summary for regions"""
        days = int(request.query_params.get('days', 30))
        region_id = request.query_params.get('region')
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        queryset = self.queryset.filter(date__gte=start_date, date__lte=end_date)
        
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        
        summary = queryset.aggregate(
            total_rainfall=models.Sum('precipitation_mm'),
            avg_temperature=Avg('temperature_avg'),
            max_temperature=Max('temperature_max'),
            min_temperature=Min('temperature_min'),
            avg_humidity=Avg('humidity_percent')
        )
        
        return Response(summary)


class DroughtRiskAssessmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Drought Risk Assessment management
    """
    queryset = DroughtRiskAssessment.objects.all()
    serializer_class = DroughtRiskAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['region', 'assessment_date', 'risk_level']
    ordering_fields = ['assessment_date', 'risk_score']
    ordering = ['-assessment_date', 'region']
    
    @action(detail=False, methods=['get'])
    def current_risk_map(self, request):
        """Get current drought risk for all regions"""
        latest_assessments = []
        regions = Region.objects.all()
        
        for region in regions:
            latest = DroughtRiskAssessment.objects.filter(
                region=region
            ).order_by('-assessment_date').first()
            
            if latest:
                latest_assessments.append(latest)
        
        serializer = self.get_serializer(latest_assessments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def risk_summary(self, request):
        """Get drought risk summary statistics"""
        latest_date = DroughtRiskAssessment.objects.aggregate(
            latest=Max('assessment_date')
        )['latest']
        
        if not latest_date:
            return Response({'message': 'No assessment data available'})
        
        latest_assessments = DroughtRiskAssessment.objects.filter(
            assessment_date=latest_date
        )
        
        risk_counts = {}
        for assessment in latest_assessments:
            level = assessment.risk_level
            risk_counts[level] = risk_counts.get(level, 0) + 1
        
        avg_risk_score = latest_assessments.aggregate(
            avg_score=Avg('risk_score')
        )['avg_score']
        
        high_risk_regions = latest_assessments.filter(
            risk_level__in=['high', 'very_high', 'extreme']
        ).count()
        
        summary = {
            'assessment_date': latest_date,
            'total_regions_assessed': latest_assessments.count(),
            'average_risk_score': avg_risk_score,
            'high_risk_regions': high_risk_regions,
            'risk_level_distribution': risk_counts
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def regional_summary(self, request):
        """Get detailed summary for all regions"""
        summaries = []
        regions = Region.objects.all()
        
        for region in regions:
            # Get latest assessment
            latest_assessment = DroughtRiskAssessment.objects.filter(
                region=region
            ).order_by('-assessment_date').first()
            
            if not latest_assessment:
                continue
            
            # Get latest NDVI and soil moisture
            latest_ndvi = NDVIData.objects.filter(
                region=region
            ).order_by('-date').first()
            
            latest_soil_moisture = SoilMoistureData.objects.filter(
                region=region
            ).order_by('-date').first()
            
            # Calculate days since last rain
            recent_weather = WeatherData.objects.filter(
                region=region,
                precipitation_mm__gt=1.0
            ).order_by('-date').first()
            
            days_since_rain = None
            if recent_weather:
                days_since_rain = (timezone.now().date() - recent_weather.date).days
            
            # Calculate trends (simplified)
            risk_trend = 'stable'  # Would need more complex calculation
            ndvi_trend = 'stable'  # Would need more complex calculation
            
            summary_data = {
                'region_id': region.id,
                'region_name': region.name,
                'current_risk_level': latest_assessment.risk_level,
                'current_risk_score': latest_assessment.risk_score,
                'last_assessment_date': latest_assessment.assessment_date,
                'latest_ndvi': latest_ndvi.ndvi_value if latest_ndvi else None,
                'latest_soil_moisture': latest_soil_moisture.moisture_percent if latest_soil_moisture else None,
                'days_since_rain': days_since_rain,
                'risk_trend': risk_trend,
                'ndvi_trend': ndvi_trend,
                'active_alerts_count': 0  # Would connect to alerts system
            }
            
            summaries.append(summary_data)
        
        serializer = RegionalDroughtSummarySerializer(summaries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def data_availability(self, request):
        """Check data availability status for all regions"""
        availability_data = []
        regions = Region.objects.all()
        
        for region in regions:
            # Check data availability
            has_ndvi = NDVIData.objects.filter(region=region).exists()
            has_soil_moisture = SoilMoistureData.objects.filter(region=region).exists()
            has_weather = WeatherData.objects.filter(region=region).exists()
            has_assessment = DroughtRiskAssessment.objects.filter(region=region).exists()
            
            # Get latest dates
            latest_ndvi = NDVIData.objects.filter(region=region).aggregate(latest=Max('date'))['latest']
            latest_soil = SoilMoistureData.objects.filter(region=region).aggregate(latest=Max('date'))['latest']
            latest_weather = WeatherData.objects.filter(region=region).aggregate(latest=Max('date'))['latest']
            latest_assessment = DroughtRiskAssessment.objects.filter(region=region).aggregate(latest=Max('assessment_date'))['latest']
            
            # Calculate completeness score
            completeness_score = sum([has_ndvi, has_soil_moisture, has_weather, has_assessment]) / 4.0
            
            availability_info = {
                'region_id': region.id,
                'region_name': region.name,
                'has_ndvi_data': has_ndvi,
                'has_soil_moisture_data': has_soil_moisture,
                'has_weather_data': has_weather,
                'has_risk_assessment': has_assessment,
                'latest_ndvi_date': latest_ndvi,
                'latest_soil_moisture_date': latest_soil,
                'latest_weather_date': latest_weather,
                'latest_assessment_date': latest_assessment,
                'ndvi_data_quality': 'good' if has_ndvi else None,
                'overall_data_completeness': completeness_score
            }
            
            availability_data.append(availability_info)
        
        serializer = DataAvailabilitySerializer(availability_data, many=True)
        return Response(serializer.data)