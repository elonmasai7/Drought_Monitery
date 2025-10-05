"""
Farmer-specific utility functions for the dashboard
"""
from django.db.models import Q, Avg, Count, Max
from django.utils import timezone
from datetime import timedelta

from core.models import UserProfile, Region
from alerts.models import Alert, AlertDelivery
from drought_data.models import DroughtRiskAssessment, WeatherData, NDVIData, SoilMoistureData


def get_farmer_dashboard_data(user):
    """
    Get personalized dashboard data for a farmer
    """
    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        # Return default data if no profile exists
        return get_default_farmer_data()
    
    # Time ranges
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Get farmer's region or nearby region
    farmer_region = user_profile.region
    if not farmer_region and user_profile.latitude and user_profile.longitude:
        # Find nearest region based on coordinates
        farmer_region = find_nearest_region(
            user_profile.latitude, 
            user_profile.longitude
        )
    
    # Regional data
    regional_data = {}
    if farmer_region:
        regional_data = get_regional_dashboard_data(farmer_region, month_ago)
    
    # Personal farm data
    farm_data = {
        'farm_size': user_profile.farm_size_acres,
        'primary_crops': user_profile.primary_crops.split(',') if user_profile.primary_crops else [],
        'location': {
            'latitude': float(user_profile.latitude) if user_profile.latitude else None,
            'longitude': float(user_profile.longitude) if user_profile.longitude else None,
        }
    }
    
    # Personalized alerts
    farmer_alerts = get_farmer_alerts(user_profile, week_ago)
    
    # Weather recommendations
    recommendations = get_farmer_recommendations(user_profile, regional_data)
    
    return {
        'profile': user_profile,
        'farm_data': farm_data,
        'regional_data': regional_data,
        'alerts': farmer_alerts,
        'recommendations': recommendations,
        'region': farmer_region,
    }


def get_regional_dashboard_data(region, since_date):
    """
    Get regional data for farmer's area
    """
    # Latest drought risk assessment
    latest_risk = DroughtRiskAssessment.objects.filter(
        region=region
    ).order_by('-assessment_date').first()
    
    # Weather data for the region
    recent_weather = WeatherData.objects.filter(
        region=region,
        date__gte=since_date
    ).aggregate(
        avg_temperature=Avg('temperature_avg'),
        avg_humidity=Avg('humidity_percent'),
        total_rainfall=Avg('precipitation_mm'),
        avg_wind_speed=Avg('wind_speed_kmh')
    )
    
    # NDVI data (vegetation health)
    recent_ndvi = NDVIData.objects.filter(
        region=region,
        date__gte=since_date
    ).aggregate(
        avg_ndvi=Avg('ndvi_value'),
        latest_date=Max('date')
    )
    
    # Soil moisture data
    recent_soil = SoilMoistureData.objects.filter(
        region=region,
        date__gte=since_date
    ).aggregate(
        avg_moisture=Avg('moisture_percent'),
        latest_date=Max('date')
    )
    
    return {
        'risk_assessment': latest_risk,
        'weather': recent_weather,
        'ndvi': recent_ndvi,
        'soil_moisture': recent_soil,
    }


def get_farmer_alerts(user_profile, since_date):
    """
    Get relevant alerts for the farmer
    """
    alerts_query = Alert.objects.filter(
        created_at__gte=since_date
    ).order_by('-created_at')
    
    # Filter by farmer's region if available
    if user_profile.region:
        alerts_query = alerts_query.filter(
            Q(region=user_profile.region) | Q(region__isnull=True)  # Include general alerts
        )
    
    # Get alert delivery status for this user
    alerts = alerts_query.select_related('region')[:20]
    
    # Check which alerts were delivered to this user
    delivered_alerts = AlertDelivery.objects.filter(
        alert__in=alerts,
        phone_number=user_profile.phone_number
    ).values_list('alert_id', flat=True)
    
    alerts_data = []
    for alert in alerts:
        alerts_data.append({
            'alert': alert,
            'delivered': alert.id in delivered_alerts,
            'relevant': is_alert_relevant_to_farmer(alert, user_profile)
        })
    
    return alerts_data


def get_farmer_recommendations(user_profile, regional_data):
    """
    Generate personalized recommendations for the farmer
    """
    recommendations = []
    
    # Risk-based recommendations
    risk_assessment = regional_data.get('risk_assessment')
    if risk_assessment:
        if risk_assessment.risk_level in ['high', 'very_high', 'extreme']:
            recommendations.append({
                'type': 'warning',
                'title': 'High Drought Risk Detected',
                'message': 'Consider water conservation measures and drought-resistant crop varieties.',
                'icon': 'fas fa-exclamation-triangle',
                'priority': 'high'
            })
        elif risk_assessment.risk_level == 'medium':
            recommendations.append({
                'type': 'info',
                'title': 'Moderate Drought Risk',
                'message': 'Monitor soil moisture and prepare for potential water scarcity.',
                'icon': 'fas fa-info-circle',
                'priority': 'medium'
            })
    
    # Weather-based recommendations
    weather = regional_data.get('weather', {})
    total_rainfall = weather.get('total_rainfall') or 0
    if total_rainfall < 10:  # Less than 10mm in the past month
        recommendations.append({
            'type': 'warning',
            'title': 'Low Rainfall Alert',
            'message': 'Rainfall has been below average. Consider irrigation planning.',
            'icon': 'fas fa-cloud-rain',
            'priority': 'high'
        })
    
    # Crop-specific recommendations
    if user_profile.primary_crops:
        crops = [crop.strip().lower() for crop in user_profile.primary_crops.split(',')]
        for crop in crops:
            if crop in ['maize', 'corn']:
                recommendations.append({
                    'type': 'success',
                    'title': f'{crop.title()} Growing Tips',
                    'message': 'Ensure adequate nitrogen fertilization during vegetative stage.',
                    'icon': 'fas fa-seedling',
                    'priority': 'low'
                })
    
    # Seasonal recommendations
    current_month = timezone.now().month
    if current_month in [3, 4, 5]:  # March-May (long rains season in Kenya)
        recommendations.append({
            'type': 'info',
            'title': 'Long Rains Season',
            'message': 'Optimal time for land preparation and planting of food crops.',
            'icon': 'fas fa-calendar-alt',
            'priority': 'medium'
        })
    elif current_month in [10, 11, 12]:  # Oct-Dec (short rains season)
        recommendations.append({
            'type': 'info',
            'title': 'Short Rains Season',
            'message': 'Good time for planting drought-tolerant crops.',
            'icon': 'fas fa-calendar-alt',
            'priority': 'medium'
        })
    
    return recommendations


def is_alert_relevant_to_farmer(alert, user_profile):
    """
    Determine if an alert is relevant to a specific farmer
    """
    # Region-based relevance
    if alert.region and user_profile.region:
        if alert.region == user_profile.region:
            return True
        # Check if it's a parent region
        if user_profile.region.parent_region == alert.region:
            return True
    
    # Crop-specific alerts
    if user_profile.primary_crops and alert.message:
        farmer_crops = [crop.strip().lower() for crop in user_profile.primary_crops.split(',')]
        alert_text = alert.message.lower()
        for crop in farmer_crops:
            if crop in alert_text:
                return True
    
    # General alerts (no specific region)
    if not alert.region:
        return True
    
    return False


def find_nearest_region(latitude, longitude):
    """
    Find the nearest region to given coordinates
    """
    # Simple distance calculation (not highly accurate but sufficient for this use case)
    import math
    
    min_distance = float('inf')
    nearest_region = None
    
    regions = Region.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    for region in regions:
        # Calculate approximate distance using Pythagorean theorem
        lat_diff = float(latitude) - float(region.latitude)
        lng_diff = float(longitude) - float(region.longitude)
        distance = math.sqrt(lat_diff**2 + lng_diff**2)
        
        if distance < min_distance:
            min_distance = distance
            nearest_region = region
    
    return nearest_region


def get_default_farmer_data():
    """
    Get default data when no user profile exists
    """
    # Get general system data
    total_alerts = Alert.objects.count()
    recent_alerts = Alert.objects.order_by('-created_at')[:5]
    
    return {
        'profile': None,
        'farm_data': {
            'farm_size': None,
            'primary_crops': [],
            'location': {'latitude': None, 'longitude': None}
        },
        'regional_data': {},
        'alerts': [{'alert': alert, 'delivered': False, 'relevant': True} for alert in recent_alerts],
        'recommendations': [
            {
                'type': 'info',
                'title': 'Complete Your Profile',
                'message': 'Add your farm details and location for personalized recommendations.',
                'icon': 'fas fa-user-edit',
                'priority': 'high'
            }
        ],
        'region': None,
    }