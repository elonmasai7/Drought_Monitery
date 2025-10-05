from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

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
]