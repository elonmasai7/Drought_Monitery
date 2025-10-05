from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register(r'regions', views.RegionViewSet)
router.register(r'users', views.UserProfileViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    # Location API
    path('api/location/', views.store_location, name='store_location'),
    # Heat map data APIs
    path('api/ndvi/', views.get_ndvi_data, name='get_ndvi_data'),
    path('api/soil_ph/', views.get_soil_ph_data, name='get_soil_ph_data'),
    
    # Role-based API endpoints
    path('api/role/', api_views.get_user_role_api, name='get_user_role'),
    path('api/admin/users/', api_views.admin_get_users, name='admin_get_users'),
    path('api/admin/system-stats/', api_views.admin_get_system_stats, name='admin_get_system_stats'),
    path('api/farmer/dashboard/', api_views.farmer_get_dashboard_data, name='farmer_get_dashboard_data'),
]