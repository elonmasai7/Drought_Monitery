"""
URL configuration for drought_warning_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

# Import all app routers
from core.views import RegionViewSet, UserProfileViewSet
from drought_data.views import NDVIDataViewSet, SoilMoistureDataViewSet, WeatherDataViewSet, DroughtRiskAssessmentViewSet
from farmers.views import FarmerProfileViewSet, FarmFieldViewSet, CropCalendarViewSet, FarmerGroupViewSet
from alerts.views import AlertTemplateViewSet, AlertViewSet, AlertDeliveryViewSet, AlertSubscriptionViewSet, AlertFeedbackViewSet

# Create main API router
router = routers.DefaultRouter()

# Core app
router.register(r'regions', RegionViewSet)
router.register(r'users', UserProfileViewSet)

# Drought data app
router.register(r'ndvi', NDVIDataViewSet)
router.register(r'soil-moisture', SoilMoistureDataViewSet)
router.register(r'weather', WeatherDataViewSet)
router.register(r'risk-assessments', DroughtRiskAssessmentViewSet)

# Farmers app
router.register(r'farmer-profiles', FarmerProfileViewSet)
router.register(r'farm-fields', FarmFieldViewSet)
router.register(r'crop-calendar', CropCalendarViewSet)
router.register(r'farmer-groups', FarmerGroupViewSet)

# Alerts app
router.register(r'alert-templates', AlertTemplateViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'alert-deliveries', AlertDeliveryViewSet)
router.register(r'alert-subscriptions', AlertSubscriptionViewSet)
router.register(r'alert-feedback', AlertFeedbackViewSet)

urlpatterns = [
    path('', lambda request: redirect('/dashboard/'), name='home'),
    path("admin/", admin.site.urls),
    
    # API endpoints
    path('api/v1/', include(router.urls)),
    path('api/auth/token/', obtain_auth_token, name='api_token_auth'),
    path('api/auth/', include('rest_framework.urls')),
    
    # App-specific URLs (for any custom endpoints)
    path('core/', include('core.urls')),
    path('drought-data/', include('drought_data.urls')),
    path('farmers/', include('farmers.urls')),
    path('alerts/', include('alerts.urls')),
    
    # Dashboard will be added later
    path('dashboard/', include('dashboard.urls')),
    
    # USSD endpoints
    # USSD endpoints
    path('ussd/', include('ussd.urls')),
    
    # Reports endpoints
    path('reports/', include('reports.urls')),
    
    # Health check endpoints
    path('health/', lambda request: __import__('core.health', fromlist=['health_check']).health_check(request), name='health_check'),
    path('health/detailed/', lambda request: __import__('core.health', fromlist=['health_detailed']).health_detailed(request), name='health_detailed'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
