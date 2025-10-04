from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'templates', views.AlertTemplateViewSet)
router.register(r'alerts', views.AlertViewSet)
router.register(r'deliveries', views.AlertDeliveryViewSet)
router.register(r'subscriptions', views.AlertSubscriptionViewSet)
router.register(r'feedback', views.AlertFeedbackViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]