from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from .models import FarmerProfile, FarmField, CropCalendar, FarmerGroup
from .serializers import (
    FarmerProfileSerializer, FarmFieldSerializer, FarmFieldSummarySerializer,
    CropCalendarSerializer, FarmerGroupSerializer, FarmerGroupMembershipSerializer,
    FarmerStatsSerializer, FarmerDashboardSerializer, PlantingAdvisorySerializer
)
from core.models import UserProfile
from drought_data.models import DroughtRiskAssessment, WeatherData


class FarmerProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing farmer profiles
    """
    queryset = FarmerProfile.objects.all()
    serializer_class = FarmerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['farming_type', 'irrigation_type', 'has_smartphone']
    search_fields = ['user_profile__user__first_name', 'user_profile__user__last_name', 'farm_name']
    ordering_fields = ['created_at', 'farm_name']
    ordering = ['user_profile__user__first_name']
    
    def get_queryset(self):
        """Filter based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # If user is not admin, only show their own profile
        if not user.is_staff:
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.user_type not in ['admin', 'extension_officer']:
                    queryset = queryset.filter(user_profile__user=user)
            except UserProfile.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's farmer profile"""
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            farmer_profile = FarmerProfile.objects.get(user_profile=user_profile)
            serializer = self.get_serializer(farmer_profile)
            return Response(serializer.data)
        except (UserProfile.DoesNotExist, FarmerProfile.DoesNotExist):
            return Response(
                {'error': 'Farmer profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get farmer dashboard data"""
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            farmer_profile = FarmerProfile.objects.get(user_profile=user_profile)
            
            # Get farm fields
            fields = FarmField.objects.filter(farmer=farmer_profile, is_active=True)
            total_fields = fields.count()
            total_area = fields.aggregate(total=Sum('area_acres'))['total'] or 0
            
            # Get active crops
            active_crops = list(fields.filter(
                current_crop__isnull=False
            ).values_list('current_crop', flat=True).distinct())
            
            # Get current drought risk for farmer's region
            current_risk = None
            if user_profile.region:
                risk_assessment = DroughtRiskAssessment.objects.filter(
                    region=user_profile.region
                ).order_by('-assessment_date').first()
                
                if risk_assessment:
                    current_risk = {
                        'risk_level': risk_assessment.risk_level,
                        'risk_score': risk_assessment.risk_score,
                        'assessment_date': risk_assessment.assessment_date,
                        'recommendations': risk_assessment.recommended_actions
                    }
            
            # Get weather summary
            weather_summary = None
            if user_profile.region:
                recent_weather = WeatherData.objects.filter(
                    region=user_profile.region,
                    date__gte=timezone.now().date() - timedelta(days=7)
                ).aggregate(
                    avg_temp=Avg('temperature_avg'),
                    total_rain=Sum('precipitation_mm'),
                    avg_humidity=Avg('humidity_percent')
                )
                
                if any(recent_weather.values()):
                    weather_summary = recent_weather
            
            # Basic recommendations
            recommendations = []
            if current_risk and current_risk['risk_level'] in ['high', 'very_high', 'extreme']:
                recommendations.append("High drought risk detected - conserve water and consider drought-resistant crops")
            
            dashboard_data = {
                'farmer_profile': farmer_profile,
                'total_fields': total_fields,
                'total_area': total_area,
                'active_crops': active_crops,
                'current_planting_season': None,  # Would need more complex logic
                'upcoming_harvests': [],  # Would calculate from planting dates
                'current_drought_risk': current_risk,
                'recent_alerts': [],  # Would connect to alerts system
                'weather_summary': weather_summary,
                'recommendations': recommendations
            }
            
            serializer = FarmerDashboardSerializer(dashboard_data)
            return Response(serializer.data)
            
        except (UserProfile.DoesNotExist, FarmerProfile.DoesNotExist):
            return Response(
                {'error': 'Farmer profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get farmer statistics"""
        total_farmers = self.queryset.count()
        active_farmers = self.queryset.filter(user_profile__is_active=True).count()
        
        # Farming type distribution
        farming_types = self.queryset.values('farming_type').annotate(
            count=Count('id')
        ).order_by('farming_type')
        farming_type_dist = {ft['farming_type']: ft['count'] for ft in farming_types}
        
        # Irrigation type distribution
        irrigation_types = self.queryset.values('irrigation_type').annotate(
            count=Count('id')
        ).order_by('irrigation_type')
        irrigation_type_dist = {it['irrigation_type']: it['count'] for it in irrigation_types}
        
        # Regional distribution
        regional = self.queryset.filter(
            user_profile__region__isnull=False
        ).values('user_profile__region__name').annotate(
            count=Count('id')
        ).order_by('user_profile__region__name')
        regional_dist = {r['user_profile__region__name']: r['count'] for r in regional}
        
        # Technology adoption
        total_with_data = self.queryset.count()
        smartphone_users = self.queryset.filter(has_smartphone=True).count()
        weather_app_users = self.queryset.filter(uses_weather_apps=True).count()
        
        smartphone_rate = smartphone_users / total_with_data if total_with_data > 0 else 0
        weather_app_rate = weather_app_users / total_with_data if total_with_data > 0 else 0
        
        # Farm sizes
        farm_size_stats = self.queryset.aggregate(
            avg_size=Avg('user_profile__farm_size_acres'),
            total_area=Sum('user_profile__farm_size_acres')
        )
        
        # Groups
        total_groups = FarmerGroup.objects.filter(is_active=True).count()
        farmers_in_groups = self.queryset.filter(farmer_groups__isnull=False).distinct().count()
        
        stats = {
            'total_farmers': total_farmers,
            'active_farmers': active_farmers,
            'farming_type_distribution': farming_type_dist,
            'irrigation_type_distribution': irrigation_type_dist,
            'regional_distribution': regional_dist,
            'smartphone_adoption_rate': smartphone_rate,
            'weather_app_usage_rate': weather_app_rate,
            'average_farm_size': farm_size_stats['avg_size'] or 0,
            'total_cultivated_area': farm_size_stats['total_area'] or 0,
            'total_farmer_groups': total_groups,
            'farmers_in_groups': farmers_in_groups
        }
        
        serializer = FarmerStatsSerializer(stats)
        return Response(serializer.data)


class FarmFieldViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing farm fields
    """
    queryset = FarmField.objects.all()
    serializer_class = FarmFieldSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['farmer', 'soil_type', 'current_crop', 'is_active']
    search_fields = ['field_name', 'current_crop']
    ordering_fields = ['created_at', 'field_name', 'area_acres']
    ordering = ['farmer', 'field_name']
    
    def get_queryset(self):
        """Filter based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # If user is not admin, only show their own fields
        if not user.is_staff:
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.user_type not in ['admin', 'extension_officer']:
                    farmer_profile = FarmerProfile.objects.get(user_profile=user_profile)
                    queryset = queryset.filter(farmer=farmer_profile)
            except (UserProfile.DoesNotExist, FarmerProfile.DoesNotExist):
                queryset = queryset.none()
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FarmFieldSummarySerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['get'])
    def my_fields(self, request):
        """Get current user's farm fields"""
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            farmer_profile = FarmerProfile.objects.get(user_profile=user_profile)
            fields = FarmField.objects.filter(farmer=farmer_profile, is_active=True)
            serializer = self.get_serializer(fields, many=True)
            return Response(serializer.data)
        except (UserProfile.DoesNotExist, FarmerProfile.DoesNotExist):
            return Response(
                {'error': 'Farmer profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class CropCalendarViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing crop calendars
    """
    queryset = CropCalendar.objects.all()
    serializer_class = CropCalendarSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['crop_name', 'region']
    search_fields = ['crop_name']
    ordering_fields = ['crop_name', 'optimal_planting_start']
    ordering = ['crop_name', 'region']
    
    @action(detail=False, methods=['get'])
    def planting_advisory(self, request):
        """Get planting advisory for a specific crop and region"""
        crop_name = request.query_params.get('crop')
        region_id = request.query_params.get('region')
        
        if not crop_name or not region_id:
            return Response(
                {'error': 'crop and region parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            crop_calendar = CropCalendar.objects.get(
                crop_name__iexact=crop_name,
                region_id=region_id
            )
        except CropCalendar.DoesNotExist:
            return Response(
                {'error': 'Crop calendar not found for this crop and region'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate planting window status
        today = timezone.now().date()
        is_optimal = (crop_calendar.optimal_planting_start <= today <= crop_calendar.optimal_planting_end)
        
        days_until_start = None
        days_until_end = None
        
        if today < crop_calendar.optimal_planting_start:
            days_until_start = (crop_calendar.optimal_planting_start - today).days
        if today < crop_calendar.optimal_planting_end:
            days_until_end = (crop_calendar.optimal_planting_end - today).days
        
        # Get drought risk for region
        risk_assessment = DroughtRiskAssessment.objects.filter(
            region_id=region_id
        ).order_by('-assessment_date').first()
        
        drought_risk_level = 'unknown'
        if risk_assessment:
            drought_risk_level = risk_assessment.risk_level
        
        # Basic recommendation logic
        if is_optimal and drought_risk_level in ['very_low', 'low']:
            recommendation = "Optimal planting conditions - proceed with planting"
        elif is_optimal and drought_risk_level in ['moderate']:
            recommendation = "Planting window open but monitor weather conditions closely"
        elif is_optimal and drought_risk_level in ['high', 'very_high', 'extreme']:
            recommendation = "Consider delaying planting or choose drought-resistant varieties"
        elif days_until_start and days_until_start > 0:
            recommendation = f"Wait {days_until_start} days for optimal planting window"
        else:
            recommendation = "Outside optimal planting window - consider alternative crops"
        
        advisory = {
            'crop_name': crop_calendar.crop_name,
            'region_name': crop_calendar.region.name,
            'is_optimal_planting_window': is_optimal,
            'days_until_optimal_start': days_until_start,
            'days_until_optimal_end': days_until_end,
            'current_soil_moisture': None,  # Would get from soil moisture data
            'recent_rainfall': None,  # Would get from weather data
            'weather_forecast': {},  # Would get from weather API
            'drought_risk_level': drought_risk_level,
            'planting_risk_score': risk_assessment.risk_score if risk_assessment else 50,
            'recommendation': recommendation,
            'alternative_crops': [],  # Would suggest based on conditions
            'irrigation_advice': "Monitor soil moisture and irrigate as needed"
        }
        
        serializer = PlantingAdvisorySerializer(advisory)
        return Response(serializer.data)


class FarmerGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing farmer groups
    """
    queryset = FarmerGroup.objects.filter(is_active=True)
    serializer_class = FarmerGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['region', 'is_active']
    search_fields = ['name', 'registration_number']
    ordering_fields = ['name', 'formation_date', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def manage_membership(self, request, pk=None):
        """Add or remove farmers from group"""
        group = self.get_object()
        serializer = FarmerGroupMembershipSerializer(data=request.data)
        
        if serializer.is_valid():
            farmer_id = serializer.validated_data['farmer_id']
            action = serializer.validated_data['action']
            
            try:
                farmer = FarmerProfile.objects.get(id=farmer_id)
                
                if action == 'add':
                    group.members.add(farmer)
                    message = f"Farmer {farmer.user_profile.full_name} added to group"
                else:  # remove
                    group.members.remove(farmer)
                    message = f"Farmer {farmer.user_profile.full_name} removed from group"
                
                return Response({'message': message})
                
            except FarmerProfile.DoesNotExist:
                return Response(
                    {'error': 'Farmer not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get group members"""
        group = self.get_object()
        members = group.members.all()
        serializer = FarmerProfileSerializer(members, many=True)
        return Response(serializer.data)