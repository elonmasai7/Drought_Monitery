from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Region, UserProfile
from .serializers import (
    RegionSerializer, RegionSummarySerializer,
    UserProfileSerializer, UserProfileCreateSerializer
)


class RegionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing regions
    """
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['region_type', 'parent_region']
    search_fields = ['name']
    ordering_fields = ['name', 'region_type', 'created_at']
    ordering = ['region_type', 'name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RegionSummarySerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['get'])
    def counties(self, request):
        """Get all counties"""
        counties = self.queryset.filter(region_type='county')
        serializer = RegionSummarySerializer(counties, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sub_regions(self, request, pk=None):
        """Get sub-regions (children) of a region"""
        region = self.get_object()
        sub_regions = Region.objects.filter(parent_region=region)
        serializer = RegionSummarySerializer(sub_regions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search regions by name or type"""
        query = request.query_params.get('q', '')
        region_type = request.query_params.get('type', '')
        
        queryset = self.queryset
        
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(parent_region__name__icontains=query)
            )
        
        if region_type:
            queryset = queryset.filter(region_type=region_type)
        
        serializer = RegionSummarySerializer(queryset, many=True)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user profiles
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user_type', 'region', 'preferred_language', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'phone_number']
    ordering_fields = ['created_at', 'user__first_name']
    ordering = ['user__first_name', 'user__last_name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserProfileCreateSerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
        """Filter based on user permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # If user is not admin, only show their own profile
        if not user.is_staff:
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.user_type not in ['admin', 'extension_officer']:
                    queryset = queryset.filter(user=user)
            except UserProfile.DoesNotExist:
                queryset = queryset.filter(user=user)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        """Update current user's profile"""
        try:
            profile = UserProfile.objects.get(user=request.user)
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(profile, data=request.data, partial=partial)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def farmers(self, request):
        """Get all farmer profiles"""
        farmers = self.queryset.filter(user_type='farmer', is_active=True)
        
        # Apply region filter if provided
        region_id = request.query_params.get('region')
        if region_id:
            farmers = farmers.filter(region_id=region_id)
        
        serializer = self.get_serializer(farmers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics"""
        total_users = self.queryset.count()
        farmers = self.queryset.filter(user_type='farmer').count()
        admins = self.queryset.filter(user_type='admin').count()
        extension_officers = self.queryset.filter(user_type='extension_officer').count()
        active_users = self.queryset.filter(is_active=True).count()
        
        # Regional distribution
        regions_data = {}
        for profile in self.queryset.filter(region__isnull=False):
            region_name = profile.region.name
            if region_name not in regions_data:
                regions_data[region_name] = 0
            regions_data[region_name] += 1
        
        stats = {
            'total_users': total_users,
            'farmers': farmers,
            'admins': admins,
            'extension_officers': extension_officers,
            'active_users': active_users,
            'regional_distribution': regions_data
        }
        
        return Response(stats)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def store_location(request):
    """
    Store user's current location
    """
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not latitude or not longitude:
            return JsonResponse({
                'error': 'Latitude and longitude are required'
            }, status=400)
        
        # Store location in user profile
        try:
            profile = UserProfile.objects.get(user=request.user)
            profile.latitude = float(latitude)
            profile.longitude = float(longitude)
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Location updated successfully',
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            })
        except UserProfile.DoesNotExist:
            return JsonResponse({
                'error': 'User profile not found'
            }, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@login_required  
def get_ndvi_data(request):
    """
    Get NDVI data for heat map visualization
    """
    from drought_data.models import NDVIData
    from django.core.serializers import serialize
    import json as json_module
    
    try:
        # Get query parameters
        region_id = request.GET.get('region')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Build query
        queryset = NDVIData.objects.all()
        
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        # Get latest data if no date range specified
        if not start_date and not end_date:
            queryset = queryset.order_by('-date')[:100]
            
        data = []
        for item in queryset:
            data.append({
                'id': item.id,
                'region': {
                    'id': item.region.id,
                    'name': item.region.name,
                    'latitude': float(item.region.latitude) if item.region.latitude else None,
                    'longitude': float(item.region.longitude) if item.region.longitude else None
                },
                'ndvi_value': float(item.ndvi_value),
                'date': item.date.isoformat(),
                'data_source': item.data_source
            })
            
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
@login_required
def get_soil_ph_data(request):
    """
    Get soil pH data for heat map visualization
    """
    from drought_data.models import SoilMoistureData
    
    try:
        # Get query parameters  
        region_id = request.GET.get('region')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Build query
        queryset = SoilMoistureData.objects.all()
        
        if region_id:
            queryset = queryset.filter(region_id=region_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date) 
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        # Get latest data if no date range specified
        if not start_date and not end_date:
            queryset = queryset.order_by('-date')[:100]
            
        data = []
        for item in queryset:
            data.append({
                'id': item.id,
                'region': {
                    'id': item.region.id,
                    'name': item.region.name,
                    'latitude': float(item.region.latitude) if item.region.latitude else None,
                    'longitude': float(item.region.longitude) if item.region.longitude else None
                },
                'moisture_percentage': float(item.moisture_percentage),
                'soil_ph': float(getattr(item, 'soil_ph', 7.0)),  # Default pH if not available
                'date': item.date.isoformat(),
                'data_source': item.data_source
            })
            
        return JsonResponse({
            'success': True,
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)