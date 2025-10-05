"""
Role-based permission decorators and utilities for the drought warning system
"""
from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

from .models import UserProfile


# Role checking functions
def is_admin_user(user):
    """Check if user is admin (staff, superuser, or admin profile)"""
    if not user.is_authenticated:
        return False
    
    # Check Django admin permissions
    if user.is_staff or user.is_superuser:
        return True
    
    # Check profile-based admin role
    try:
        user_profile = UserProfile.objects.get(user=user)
        return user_profile.user_type == 'admin'
    except UserProfile.DoesNotExist:
        return False


def is_farmer_user(user):
    """Check if user is a farmer"""
    if not user.is_authenticated:
        return False
    
    try:
        user_profile = UserProfile.objects.get(user=user)
        return user_profile.user_type == 'farmer'
    except UserProfile.DoesNotExist:
        # Default to farmer if no profile exists (for backwards compatibility)
        return not (user.is_staff or user.is_superuser)


def is_extension_officer(user):
    """Check if user is an extension officer"""
    if not user.is_authenticated:
        return False
    
    try:
        user_profile = UserProfile.objects.get(user=user)
        return user_profile.user_type == 'extension_officer'
    except UserProfile.DoesNotExist:
        return False


def is_admin_or_extension_officer(user):
    """Check if user is admin or extension officer"""
    return is_admin_user(user) or is_extension_officer(user)


def has_role(user, roles):
    """Check if user has any of the specified roles"""
    if not user.is_authenticated:
        return False
    
    if isinstance(roles, str):
        roles = [roles]
    
    role_checkers = {
        'admin': is_admin_user,
        'farmer': is_farmer_user,
        'extension_officer': is_extension_officer,
    }
    
    return any(role_checkers.get(role, lambda u: False)(user) for role in roles)


# Decorators
def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that require admin access.
    Redirects to login if not authenticated, shows 403 if not admin.
    """
    def check_admin(user):
        if not user.is_authenticated:
            return False
        if not is_admin_user(user):
            raise PermissionDenied("Admin access required")
        return True
    
    actual_decorator = user_passes_test(
        check_admin,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    
    if function:
        return actual_decorator(function)
    return actual_decorator


def farmer_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that require farmer access.
    """
    def check_farmer(user):
        if not user.is_authenticated:
            return False
        if not is_farmer_user(user):
            raise PermissionDenied("Farmer access required")
        return True
    
    actual_decorator = user_passes_test(
        check_farmer,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    
    if function:
        return actual_decorator(function)
    return actual_decorator


def extension_officer_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that require extension officer access.
    """
    def check_extension_officer(user):
        if not user.is_authenticated:
            return False
        if not is_extension_officer(user):
            raise PermissionDenied("Extension officer access required")
        return True
    
    actual_decorator = user_passes_test(
        check_extension_officer,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    
    if function:
        return actual_decorator(function)
    return actual_decorator


def role_required(*roles):
    """
    Decorator that requires user to have one of the specified roles.
    Usage: @role_required('admin', 'extension_officer')
    """
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('dashboard:login')
            
            if not has_role(request.user, roles):
                if request.is_ajax() or request.content_type == 'application/json':
                    return JsonResponse({
                        'error': 'Permission denied',
                        'required_roles': list(roles)
                    }, status=403)
                else:
                    raise PermissionDenied(f"Access requires one of: {', '.join(roles)}")
            
            return function(request, *args, **kwargs)
        return wrapper
    return decorator


def api_role_required(*roles):
    """
    Decorator for API views that require specific roles.
    Returns JSON error responses instead of redirects.
    """
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Authentication required',
                    'redirect': reverse('dashboard:login')
                }, status=401)
            
            if not has_role(request.user, roles):
                return JsonResponse({
                    'error': 'Permission denied',
                    'required_roles': list(roles),
                    'user_role': get_user_role(request.user)
                }, status=403)
            
            return function(request, *args, **kwargs)
        return wrapper
    return decorator


def get_user_role(user):
    """Get the primary role of a user"""
    if not user.is_authenticated:
        return None
    
    if user.is_superuser:
        return 'superuser'
    if user.is_staff:
        return 'admin'
    
    try:
        user_profile = UserProfile.objects.get(user=user)
        return user_profile.user_type
    except UserProfile.DoesNotExist:
        return 'farmer'  # Default role


def get_user_permissions(user):
    """Get a list of permissions for a user based on their role"""
    if not user.is_authenticated:
        return []
    
    role = get_user_role(user)
    
    permissions = {
        'superuser': [
            'admin_dashboard', 'user_management', 'alert_management', 'data_management',
            'system_configuration', 'farmer_dashboard', 'view_all_data', 'export_data',
            'send_alerts', 'delete_users', 'modify_system_settings'
        ],
        'admin': [
            'admin_dashboard', 'user_management', 'alert_management', 'data_management',
            'farmer_dashboard', 'view_all_data', 'export_data', 'send_alerts'
        ],
        'extension_officer': [
            'admin_dashboard', 'farmer_support', 'regional_alerts', 'farmer_dashboard',
            'view_regional_data', 'send_regional_alerts'
        ],
        'farmer': [
            'farmer_dashboard', 'view_own_data', 'update_profile', 'receive_alerts'
        ]
    }
    
    return permissions.get(role, permissions['farmer'])


def has_permission(user, permission):
    """Check if user has a specific permission"""
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def permission_required(permission):
    """
    Decorator that checks if user has a specific permission
    """
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('dashboard:login')
            
            if not has_permission(request.user, permission):
                raise PermissionDenied(f"Permission '{permission}' required")
            
            return function(request, *args, **kwargs)
        return wrapper
    return decorator


class RoleBasedAccessMixin:
    """
    Mixin for class-based views to add role-based access control
    """
    required_roles = []
    required_permissions = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dashboard:login')
        
        # Check roles
        if self.required_roles and not has_role(request.user, self.required_roles):
            raise PermissionDenied(f"Access requires one of: {', '.join(self.required_roles)}")
        
        # Check permissions
        if self.required_permissions:
            for permission in self.required_permissions:
                if not has_permission(request.user, permission):
                    raise PermissionDenied(f"Permission '{permission}' required")
        
        return super().dispatch(request, *args, **kwargs)


def smart_redirect_after_login(user):
    """
    Intelligently redirect user after login based on their role and context
    """
    role = get_user_role(user)
    
    if role in ['admin', 'superuser']:
        return reverse('dashboard:admin_dashboard')
    elif role == 'extension_officer':
        return reverse('dashboard:admin_dashboard')  # Extension officers use admin interface
    else:  # farmer or default
        return reverse('dashboard:react_dashboard')


# Context processor for templates
def role_context_processor(request):
    """
    Context processor that adds role information to all templates
    """
    if request.user.is_authenticated:
        return {
            'user_role': get_user_role(request.user),
            'user_permissions': get_user_permissions(request.user),
            'is_admin': is_admin_user(request.user),
            'is_farmer': is_farmer_user(request.user),
            'is_extension_officer': is_extension_officer(request.user),
        }
    return {
        'user_role': None,
        'user_permissions': [],
        'is_admin': False,
        'is_farmer': False,
        'is_extension_officer': False,
    }


# Middleware for role-based URL filtering
class RoleBasedURLMiddleware:
    """
    Middleware that enforces role-based URL access
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define URL patterns that require specific roles
        self.protected_patterns = {
            'admin/': ['admin', 'superuser'],
            'dashboard/admin/': ['admin', 'extension_officer', 'superuser'],
            'api/admin/': ['admin', 'extension_officer', 'superuser'],
        }
    
    def __call__(self, request):
        # Check URL protection before processing the request
        if request.user.is_authenticated:
            path = request.path_info.lstrip('/')
            
            for pattern, required_roles in self.protected_patterns.items():
                if path.startswith(pattern):
                    if not has_role(request.user, required_roles):
                        if request.is_ajax() or 'api/' in path:
                            return JsonResponse({
                                'error': 'Access denied',
                                'required_roles': required_roles
                            }, status=403)
                        else:
                            return HttpResponseForbidden(
                                f"Access denied. Required roles: {', '.join(required_roles)}"
                            )
        
        response = self.get_response(request)
        return response