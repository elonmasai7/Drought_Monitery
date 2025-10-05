from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'profiles', views.FarmerProfileViewSet)
router.register(r'fields', views.FarmFieldViewSet)
router.register(r'crop-calendar', views.CropCalendarViewSet)
router.register(r'groups', views.FarmerGroupViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]