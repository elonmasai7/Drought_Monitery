from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Main dashboard views
    path('', views.dashboard_home, name='home'),
    path('map/', views.risk_map, name='map'),
    path('analytics/', views.analytics, name='analytics'),
    path('alerts/', views.alerts_dashboard, name='alerts'),
    
    # Admin views
    path('admin/users/', views.admin_user_management, name='admin_users'),
    path('admin/create-alert/', views.create_alert, name='create_alert'),
    path('admin/test-services/', views.test_alert_services, name='test_alert_services'),
    
    # Enhanced admin views
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/alerts/', views.admin_alert_management, name='admin_alerts'),
    path('admin/farmers/', views.admin_farmer_management, name='admin_farmers'),
    path('admin/ussd/', views.admin_ussd_analytics, name='admin_ussd'),
    path('admin/data/', views.admin_data_management, name='admin_data'),
    path('admin/bulk-alert/', views.admin_bulk_alert, name='admin_bulk_alert'),
    path('admin/export/', views.admin_export_data, name='admin_export'),
    
    # API endpoints for dashboard data
    path('api/risk-trends/', views.api_risk_trends, name='api_risk_trends'),
    path('api/ndvi-trends/', views.api_ndvi_trends, name='api_ndvi_trends'),
    path('api/soil-moisture-trends/', views.api_soil_moisture_trends, name='api_soil_moisture_trends'),
    path('api/weather-data/', views.api_weather_data, name='api_weather_data'),
    path('api/regional-summary/', views.api_regional_summary, name='api_regional_summary'),
]