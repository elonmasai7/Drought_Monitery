"""
API views for core functionality including user role management
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
import json

from .models import UserProfile, Region
from .permissions import get_user_role, get_user_permissions, has_role
from .serializers import UserProfileSerializer, RegionSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    """
    Get current user's profile information including role
    """
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(user_profile)
        
        # Add role and permissions information
        profile_data = serializer.data
        profile_data.update({
            'user_role': get_user_role(request.user),
            'permissions': get_user_permissions(request.user),
            'is_admin': has_role(request.user, ['admin', 'superuser']),
            'is_farmer': has_role(request.user, ['farmer']),
            'is_extension_officer': has_role(request.user, ['extension_officer']),
        })
        
        return Response(profile_data)
        
    except UserProfile.DoesNotExist:
        # Create a basic profile for users without one
        user_profile = UserProfile.objects.create(
            user=request.user,
            user_type='farmer',  # Default to farmer
            phone_number='',
        )
        
        serializer = UserProfileSerializer(user_profile)
        profile_data = serializer.data
        profile_data.update({
            'user_role': get_user_role(request.user),
            'permissions': get_user_permissions(request.user),
            'is_admin': has_role(request.user, ['admin', 'superuser']),
            'is_farmer': has_role(request.user, ['farmer']),
            'is_extension_officer': has_role(request.user, ['extension_officer']),
        })
        
        return Response(profile_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_location_api(request):
    """
    Update user's location coordinates
    """
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(
            user=request.user,
            user_type='farmer',
            phone_number='',
        )
    
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    
    if latitude is not None and longitude is not None:
        user_profile.latitude = latitude
        user_profile.longitude = longitude
        user_profile.save()
        
        return Response({
            'success': True,
            'message': 'Location updated successfully',
            'latitude': float(user_profile.latitude),
            'longitude': float(user_profile.longitude)
        })
    else:
        return Response({
            'success': False,
            'message': 'Invalid latitude or longitude'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_regions_api(request):
    """
    Get regions available to the user based on their role
    """
    user_role = get_user_role(request.user)
    
    if user_role in ['admin', 'superuser']:
        # Admins can see all regions
        regions = Region.objects.all()
    elif user_role == 'extension_officer':
        # Extension officers can see regions they're assigned to
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            if user_profile.region:
                # Show assigned region and its children
                regions = Region.objects.filter(
                    Q(id=user_profile.region.id) |
                    Q(parent_region=user_profile.region)
                )
            else:
                regions = Region.objects.filter(region_type='county')
        except UserProfile.DoesNotExist:
            regions = Region.objects.filter(region_type='county')
    else:
        # Farmers see county-level regions
        regions = Region.objects.filter(region_type='county')
    
    serializer = RegionSerializer(regions, many=True)
    return Response(serializer.data)


@login_required
@require_http_methods(["GET"])
def user_role_info(request):
    """
    Simple endpoint to get user role information (non-DRF)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    role_info = {
        'user_id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'full_name': request.user.get_full_name(),
        'role': get_user_role(request.user),
        'permissions': get_user_permissions(request.user),
        'is_admin': has_role(request.user, ['admin', 'superuser']),
        'is_farmer': has_role(request.user, ['farmer']),
        'is_extension_officer': has_role(request.user, ['extension_officer']),
    }
    
    # Add profile information if available
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        role_info.update({
            'phone_number': user_profile.phone_number,
            'region_id': user_profile.region.id if user_profile.region else None,
            'region_name': user_profile.region.name if user_profile.region else None,
            'location': {
                'latitude': float(user_profile.latitude) if user_profile.latitude else None,
                'longitude': float(user_profile.longitude) if user_profile.longitude else None
            },
            'farm_size_acres': user_profile.farm_size_acres,
            'primary_crops': user_profile.primary_crops.split(',') if user_profile.primary_crops else [],
            'preferred_language': user_profile.preferred_language,
        })
    except UserProfile.DoesNotExist:
        pass
    
    return JsonResponse(role_info)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def check_permission(request):
    """
    Check if current user has specific permission
    """
    try:
        data = json.loads(request.body)
        permission = data.get('permission')
        
        if not permission:
            return JsonResponse({'error': 'Permission parameter required'}, status=400)
        
        user_permissions = get_user_permissions(request.user)
        has_perm = permission in user_permissions
        
        return JsonResponse({
            'has_permission': has_perm,
            'permission': permission,
            'user_permissions': user_permissions,
            'user_role': get_user_role(request.user)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_config_api(request):
    """
    Get dashboard configuration based on user role
    """
    user_role = get_user_role(request.user)
    
    # Base configuration
    config = {
        'user_role': user_role,
        'features': {
            'maps': True,
            'alerts': True,
            'weather': True,
        },
        'navigation': [],
        'quick_actions': []
    }
    
    # Role-specific configuration
    if user_role in ['admin', 'superuser']:
        config['features'].update({
            'user_management': True,
            'system_settings': True,
            'data_management': True,
            'bulk_alerts': True,
            'analytics': True,
        })
        config['navigation'] = [
            {'name': 'Dashboard', 'url': '/dashboard/admin/', 'icon': 'dashboard'},
            {'name': 'Users', 'url': '/dashboard/admin/users/', 'icon': 'users'},
            {'name': 'Alerts', 'url': '/dashboard/admin/alerts/', 'icon': 'bell'},
            {'name': 'Analytics', 'url': '/dashboard/analytics/', 'icon': 'chart'},
            {'name': 'Data', 'url': '/dashboard/admin/data/', 'icon': 'database'},
        ]
        config['quick_actions'] = [
            {'name': 'Send Alert', 'url': '/dashboard/admin/create-alert/', 'icon': 'alert'},
            {'name': 'Export Data', 'url': '/dashboard/admin/export/', 'icon': 'download'},
        ]
        
    elif user_role == 'extension_officer':
        config['features'].update({
            'farmer_support': True,
            'regional_alerts': True,
            'regional_analytics': True,
        })
        config['navigation'] = [
            {'name': 'Dashboard', 'url': '/dashboard/admin/', 'icon': 'dashboard'},
            {'name': 'Farmers', 'url': '/dashboard/admin/farmers/', 'icon': 'users'},
            {'name': 'Alerts', 'url': '/dashboard/admin/alerts/', 'icon': 'bell'},
            {'name': 'Analytics', 'url': '/dashboard/analytics/', 'icon': 'chart'},
        ]
        config['quick_actions'] = [
            {'name': 'Support Farmers', 'url': '/dashboard/admin/farmers/', 'icon': 'help'},
            {'name': 'Send Alert', 'url': '/dashboard/admin/create-alert/', 'icon': 'alert'},
        ]
        
    else:  # farmer
        config['features'].update({
            'farm_management': True,
            'personalized_recommendations': True,
            'crop_calendar': True,
        })
        config['navigation'] = [
            {'name': 'Dashboard', 'url': '/dashboard/react/', 'icon': 'home'},
            {'name': 'Map', 'url': '/dashboard/map/', 'icon': 'map'},
            {'name': 'Profile', 'url': '/dashboard/profile/', 'icon': 'user'},
        ]
        config['quick_actions'] = [
            {'name': 'Update Location', 'url': '/dashboard/profile/', 'icon': 'location'},
            {'name': 'View Alerts', 'url': '/dashboard/react/#alerts', 'icon': 'bell'},
        ]
    
    return Response(config)


# Role-based API endpoints referenced in URLs
@login_required
@require_http_methods(["GET"])
def get_user_role_api(request):
    """
    Simple endpoint to get user role (referenced in URLs)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    from .permissions import get_user_role as get_role_helper
    
    return JsonResponse({
        'role': get_role_helper(request.user),
        'username': request.user.username,
        'is_admin': has_role(request.user, ['admin', 'superuser']),
        'is_farmer': has_role(request.user, ['farmer']),
        'is_extension_officer': has_role(request.user, ['extension_officer']),
    })


@login_required
@require_http_methods(["GET"])
def admin_get_users(request):
    """
    Admin endpoint to get list of users
    """
    # Check admin permission
    if not has_role(request.user, ['admin', 'superuser']):
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    # Imports moved to top of file
    
    # Get query parameters
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    # Base query
    users = User.objects.select_related('userprofile').order_by('-date_joined')
    
    # Apply search filter
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Apply role filter
    if role_filter:
        if role_filter == 'admin':
            users = users.filter(Q(is_staff=True) | Q(is_superuser=True))
        elif role_filter in ['farmer', 'extension_officer']:
            users = users.filter(userprofile__user_type=role_filter)
    
    # Paginate
    paginator = Paginator(users, per_page)
    page_obj = paginator.get_page(page)
    
    # Serialize users
    users_data = []
    for user in page_obj:
        profile = getattr(user, 'userprofile', None)
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.get_full_name(),
            'role': get_user_role(user),
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_active': user.is_active,
            'phone_number': profile.phone_number if profile else None,
            'region': profile.region.name if profile and profile.region else None,
        })
    
    return JsonResponse({
        'users': users_data,
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_users': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })


@login_required
@require_http_methods(["GET"])
def admin_get_system_stats(request):
    """
    Admin endpoint to get system statistics
    """
    # Check admin permission
    if not has_role(request.user, ['admin', 'superuser']):
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    # Imports moved to top of file
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User statistics
    total_users = User.objects.count()
    admin_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).count()
    farmer_users = User.objects.filter(userprofile__user_type='farmer').count()
    extension_officers = User.objects.filter(userprofile__user_type='extension_officer').count()
    
    # Recent activity
    new_users_week = User.objects.filter(date_joined__date__gte=week_ago).count()
    active_users_week = User.objects.filter(last_login__date__gte=week_ago).count()
    
    # System health (basic)
    stats = {
        'users': {
            'total': total_users,
            'admins': admin_users,
            'farmers': farmer_users,
            'extension_officers': extension_officers,
            'new_this_week': new_users_week,
            'active_this_week': active_users_week,
        },
        'system': {
            'regions': Region.objects.count(),
            'uptime': '99.9%',  # Placeholder
            'last_backup': today.isoformat(),  # Placeholder
        },
        'activity': {
            'total_logins_week': active_users_week,
            'avg_session_duration': '25 minutes',  # Placeholder
        }
    }
    
    # Add alert statistics if alerts app is available
    try:
        from alerts.models import Alert
        stats['alerts'] = {
            'total': Alert.objects.count(),
            'sent_this_week': Alert.objects.filter(created_at__date__gte=week_ago).count(),
            'pending': Alert.objects.filter(status='pending').count(),
        }
    except ImportError:
        pass
    
    return JsonResponse(stats)


@login_required
@require_http_methods(["GET"])
def farmer_get_dashboard_data(request):
    """
    Farmer endpoint to get personalized dashboard data
    """
    # Check farmer permission
    if not has_role(request.user, ['farmer']):
        return JsonResponse({'error': 'Farmer access required'}, status=403)
    
    try:
        from dashboard.farmer_utils import get_farmer_dashboard_data
        dashboard_data = get_farmer_dashboard_data(request.user)
        return JsonResponse(dashboard_data)
    except ImportError:
        # Fallback if farmer_utils not available
        return JsonResponse({
            'recommendations': [],
            'weather': {},
            'alerts': [],
            'tips': [],
            'message': 'Farmer dashboard data not available'
        })