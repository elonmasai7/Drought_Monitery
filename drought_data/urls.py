from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'ndvi', views.NDVIDataViewSet)
router.register(r'soil-moisture', views.SoilMoistureDataViewSet)
router.register(r'weather', views.WeatherDataViewSet)
router.register(r'risk-assessments', views.DroughtRiskAssessmentViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]