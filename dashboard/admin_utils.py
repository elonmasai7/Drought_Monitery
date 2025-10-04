"""
Administrative utility functions for the dashboard
"""
from django.contrib.auth.models import User
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta

from core.models import UserProfile, Region
from alerts.models import Alert, AlertDelivery
from farmers.models import FarmerProfile
from drought_data.models import DroughtRiskAssessment, WeatherData, NDVIData, SoilMoistureData
from ussd.models import USSDSession, USSDUser


def get_system_overview():
    """
    Get comprehensive system overview statistics
    """
    # Time ranges
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    overview = {
        'users': {
            'total': User.objects.count(),
            'active_last_30_days': User.objects.filter(last_login__gte=now - timedelta(days=30)).count(),
            'farmers': UserProfile.objects.filter(user_type='farmer').count(),
            'extension_officers': UserProfile.objects.filter(user_type='extension_officer').count(),
            'admins': User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).count(),
        },
        'alerts': {
            'total': Alert.objects.count(),
            'sent_today': Alert.objects.filter(sent_at__date=today).count(),
            'sent_this_week': Alert.objects.filter(sent_at__date__gte=week_ago).count(),
            'pending': Alert.objects.filter(status__in=['draft', 'scheduled']).count(),
            'failed': Alert.objects.filter(status='failed').count(),
        },
        'data': {
            'weather_records': WeatherData.objects.count(),
            'ndvi_records': NDVIData.objects.count(),
            'soil_moisture_records': SoilMoistureData.objects.count(),
            'risk_assessments': DroughtRiskAssessment.objects.count(),
            'latest_weather': WeatherData.objects.filter(date__gte=week_ago).count(),
            'latest_ndvi': NDVIData.objects.filter(date__gte=month_ago).count(),
        },
        'ussd': {
            'total_sessions': USSDSession.objects.count(),
            'active_sessions': USSDSession.objects.filter(is_active=True).count(),
            'registered_users': USSDUser.objects.count(),
            'sessions_today': USSDSession.objects.filter(started_at__date=today).count(),
        },
        'regions': {
            'total': Region.objects.count(),
            'counties': Region.objects.filter(region_type='county').count(),
            'subcounties': Region.objects.filter(region_type='subcounty').count(),
        }
    }
    
    return overview


def get_alert_management_data():
    """
    Get comprehensive alert management data
    """
    alerts = Alert.objects.select_related('region', 'created_by').order_by('-created_at')[:50]
    
    # Alert statistics by status
    alert_stats = Alert.objects.values('status').annotate(count=Count('id'))
    status_counts = {stat['status']: stat['count'] for stat in alert_stats}
    
    # Alert statistics by priority
    priority_stats = Alert.objects.values('priority').annotate(count=Count('id'))
    priority_counts = {stat['priority']: stat['count'] for stat in priority_stats}
    
    # Recent delivery statistics
    recent_deliveries = AlertDelivery.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).values('status').annotate(count=Count('id'))
    delivery_stats = {stat['status']: stat['count'] for stat in recent_deliveries}
    
    return {
        'alerts': alerts,
        'status_counts': status_counts,
        'priority_counts': priority_counts,
        'delivery_stats': delivery_stats,
        'regions': Region.objects.filter(region_type='county').order_by('name'),
    }


def get_farmer_management_data():
    """
    Get comprehensive farmer management data
    """
    farmers = User.objects.filter(
        userprofile__user_type='farmer'
    ).select_related('userprofile').order_by('-date_joined')[:100]
    
    # Farmer statistics by region
    farmer_regions = UserProfile.objects.filter(
        user_type='farmer'
    ).values('region__name').annotate(count=Count('id')).order_by('-count')
    
    # Farmer registration trends (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    registration_trend = User.objects.filter(
        userprofile__user_type='farmer',
        date_joined__gte=thirty_days_ago
    ).extra(
        select={'day': 'DATE(date_joined)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # USSD farmer data
    ussd_farmers = USSDUser.objects.select_related('region').order_by('-registration_date')[:50]
    
    return {
        'farmers': farmers,
        'farmer_regions': farmer_regions,
        'registration_trend': list(registration_trend),
        'ussd_farmers': ussd_farmers,
        'total_farmers': farmers.count(),
        'regions': Region.objects.filter(region_type='county').order_by('name'),
    }


def get_data_quality_report():
    """
    Generate data quality and system health report
    """
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    
    # Data freshness checks
    latest_weather = WeatherData.objects.aggregate(
        latest_date=timezone.models.Max('date'),
        count_last_week=Count('id', filter=Q(date__gte=week_ago))
    )
    
    latest_ndvi = NDVIData.objects.aggregate(
        latest_date=timezone.models.Max('date'),
        count_last_month=Count('id', filter=Q(date__gte=today - timedelta(days=30)))
    )
    
    latest_soil = SoilMoistureData.objects.aggregate(
        latest_date=timezone.models.Max('date'),
        count_last_week=Count('id', filter=Q(date__gte=week_ago))
    )
    
    # Risk assessment coverage
    regions_with_recent_assessments = DroughtRiskAssessment.objects.filter(
        assessment_date__gte=week_ago
    ).values('region').distinct().count()
    
    total_regions = Region.objects.filter(region_type='county').count()
    assessment_coverage = (regions_with_recent_assessments / total_regions * 100) if total_regions > 0 else 0
    
    # Alert delivery success rates
    recent_deliveries = AlertDelivery.objects.filter(
        created_at__gte=week_ago
    ).aggregate(
        total=Count('id'),
        successful=Count('id', filter=Q(status='delivered')),
        failed=Count('id', filter=Q(status='failed'))
    )
    
    delivery_success_rate = 0
    if recent_deliveries['total'] > 0:
        delivery_success_rate = (recent_deliveries['successful'] / recent_deliveries['total'] * 100)
    
    return {
        'weather_data': {
            'latest_date': latest_weather['latest_date'],
            'records_last_week': latest_weather['count_last_week'],
            'is_fresh': latest_weather['latest_date'] and (today - latest_weather['latest_date']).days <= 2 if latest_weather['latest_date'] else False
        },
        'ndvi_data': {
            'latest_date': latest_ndvi['latest_date'],
            'records_last_month': latest_ndvi['count_last_month'],
            'is_fresh': latest_ndvi['latest_date'] and (today - latest_ndvi['latest_date']).days <= 14 if latest_ndvi['latest_date'] else False
        },
        'soil_data': {
            'latest_date': latest_soil['latest_date'],
            'records_last_week': latest_soil['count_last_week'],
            'is_fresh': latest_soil['latest_date'] and (today - latest_soil['latest_date']).days <= 7 if latest_soil['latest_date'] else False
        },
        'assessment_coverage': round(assessment_coverage, 1),
        'delivery_success_rate': round(delivery_success_rate, 1),
        'total_regions': total_regions,
        'regions_assessed_recently': regions_with_recent_assessments,
    }


def get_ussd_analytics():
    """
    Get USSD system analytics
    """
    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    
    # Session statistics
    total_sessions = USSDSession.objects.count()
    active_sessions = USSDSession.objects.filter(is_active=True).count()
    sessions_today = USSDSession.objects.filter(started_at__date=today).count()
    sessions_this_week = USSDSession.objects.filter(started_at__date__gte=week_ago).count()
    
    # User statistics
    total_ussd_users = USSDUser.objects.count()
    new_users_this_week = USSDUser.objects.filter(registration_date__date__gte=week_ago).count()
    
    # Session completion rates
    completed_sessions = USSDSession.objects.filter(current_state='ended').count()
    completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    # Popular menu options (based on session states)
    menu_usage = USSDSession.objects.exclude(
        current_state__in=['main_menu', 'ended']
    ).values('current_state').annotate(count=Count('id')).order_by('-count')
    
    # Average session duration and requests
    avg_stats = USSDSession.objects.filter(
        ended_at__isnull=False
    ).aggregate(
        avg_requests=Avg('total_requests'),
        total_sessions=Count('id')
    )
    
    return {
        'session_stats': {
            'total': total_sessions,
            'active': active_sessions,
            'today': sessions_today,
            'this_week': sessions_this_week,
            'completion_rate': round(completion_rate, 1)
        },
        'user_stats': {
            'total': total_ussd_users,
            'new_this_week': new_users_this_week
        },
        'menu_usage': list(menu_usage),
        'avg_requests_per_session': round(avg_stats['avg_requests'] or 0, 1),
    }
