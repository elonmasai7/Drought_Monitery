"""
Custom middleware for the drought warning system
"""
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

from .permissions import has_role, get_user_role


class RoleBasedAccessMiddleware:
    """
    Middleware that enforces role-based access control for specific URL patterns
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define URL patterns that require specific roles
        self.protected_patterns = {
            # Admin-only areas
            '/admin/': ['admin', 'superuser'],
            '/dashboard/admin/': ['admin', 'extension_officer', 'superuser'],
            
            # API endpoints by role
            '/api/admin/': ['admin', 'extension_officer', 'superuser'],
            '/api/farmer/': ['farmer', 'admin', 'extension_officer', 'superuser'],
            
            # Dashboard areas
            '/dashboard/react/': ['farmer', 'admin', 'extension_officer', 'superuser'],
        }
        
        # Paths that don't require authentication
        self.public_paths = [
            '/dashboard/login/',
            '/dashboard/logout/',
            '/health/',
            '/static/',
            '/media/',
        ]
    
    def __call__(self, request):
        # Skip processing for public paths
        if any(request.path.startswith(path) for path in self.public_paths):
            return self.get_response(request)
        
        # Skip if user is not authenticated (let login_required handle it)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Check protected patterns
        for pattern, required_roles in self.protected_patterns.items():
            if request.path.startswith(pattern):
                if not has_role(request.user, required_roles):
                    user_role = get_user_role(request.user)
                    
                    # Handle AJAX/API requests with JSON response
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                       request.content_type == 'application/json' or \
                       request.path.startswith('/api/'):
                        return JsonResponse({
                            'error': 'Access denied',
                            'message': f'This resource requires one of the following roles: {", ".join(required_roles)}',
                            'user_role': user_role,
                            'required_roles': required_roles
                        }, status=403)
                    
                    # Handle regular HTTP requests
                    else:
                        # Redirect admin users trying to access farmer areas to admin dashboard
                        if user_role in ['admin', 'superuser'] and '/dashboard/react/' in request.path:
                            return redirect('dashboard:admin_dashboard')
                        
                        # Redirect farmers trying to access admin areas to farmer dashboard
                        elif user_role == 'farmer' and '/dashboard/admin/' in request.path:
                            return redirect('dashboard:react_dashboard')
                        
                        # Generic access denied for other cases
                        else:
                            return HttpResponseForbidden(
                                f'Access denied. Required roles: {", ".join(required_roles)}. '
                                f'Your role: {user_role}'
                            )
        
        return self.get_response(request)


class UserRoleContextMiddleware:
    """
    Middleware that adds user role information to all requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add role information to request for easy access in views
        if request.user.is_authenticated:
            request.user_role = get_user_role(request.user)
            request.is_admin = has_role(request.user, ['admin', 'superuser'])
            request.is_farmer = has_role(request.user, ['farmer'])
            request.is_extension_officer = has_role(request.user, ['extension_officer'])
        else:
            request.user_role = None
            request.is_admin = False
            request.is_farmer = False
            request.is_extension_officer = False
        
        return self.get_response(request)


class APIRoleMiddleware:
    """
    Middleware specifically for API endpoints to handle role-based access
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only process API requests
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Skip authentication endpoints
        if request.path.startswith('/api/auth/'):
            return self.get_response(request)
        
        # Check authentication for all other API endpoints
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'You must be logged in to access this API endpoint',
                'login_url': reverse('dashboard:login')
            }, status=401)
        
        # Add role information to request
        request.user_role = get_user_role(request.user)
        
        return self.get_response(request)