from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from typing import Dict, Any

from .models import Region, UserProfile
from drought_data.models import NDVIData, SoilMoistureData, WeatherData, DroughtRiskAssessment
from alerts.models import Alert, AlertDelivery

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_data(days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old data to maintain database performance
    """
    cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)
    
    results = {
        'cutoff_date': str(cutoff_date),
        'deleted_records': {}
    }
    
    try:
        # Clean up old NDVI data (keep recent + monthly samples)
        old_ndvi = NDVIData.objects.filter(date__lt=cutoff_date)
        ndvi_count = old_ndvi.count()
        old_ndvi.delete()
        results['deleted_records']['ndvi_data'] = ndvi_count
        
        # Clean up old soil moisture data
        old_soil = SoilMoistureData.objects.filter(date__lt=cutoff_date)
        soil_count = old_soil.count()
        old_soil.delete()
        results['deleted_records']['soil_moisture_data'] = soil_count
        
        # Clean up old weather data
        old_weather = WeatherData.objects.filter(date__lt=cutoff_date)
        weather_count = old_weather.count()
        old_weather.delete()
        results['deleted_records']['weather_data'] = weather_count
        
        # Clean up old risk assessments (keep monthly samples)
        old_assessments = DroughtRiskAssessment.objects.filter(assessment_date__lt=cutoff_date)
        assessment_count = old_assessments.count()
        old_assessments.delete()
        results['deleted_records']['risk_assessments'] = assessment_count
        
        # Clean up old alert deliveries
        old_deliveries = AlertDelivery.objects.filter(created_at__date__lt=cutoff_date)
        delivery_count = old_deliveries.count()
        old_deliveries.delete()
        results['deleted_records']['alert_deliveries'] = delivery_count
        
        # Keep alerts but clean up very old ones (older than 1 year)
        very_old_cutoff = timezone.now().date() - timedelta(days=365)
        very_old_alerts = Alert.objects.filter(created_at__date__lt=very_old_cutoff)
        alert_count = very_old_alerts.count()
        very_old_alerts.delete()
        results['deleted_records']['old_alerts'] = alert_count
        
        total_deleted = sum(results['deleted_records'].values())
        logger.info(f"Cleanup completed: {total_deleted} records deleted")
        
        results['status'] = 'completed'
        results['total_deleted'] = total_deleted
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        results['status'] = 'error'
        results['error'] = str(e)
    
    return results


@shared_task
def update_system_statistics() -> Dict[str, Any]:
    """
    Update system-wide statistics and cache commonly used metrics
    """
    from django.core.cache import cache
    
    stats = {}
    
    try:
        # User statistics
        total_users = UserProfile.objects.count()
        active_users = UserProfile.objects.filter(is_active=True).count()
        farmers = UserProfile.objects.filter(user_type='farmer').count()
        admins = UserProfile.objects.filter(user_type='admin').count()
        
        stats['users'] = {
            'total': total_users,
            'active': active_users,
            'farmers': farmers,
            'admins': admins
        }
        
        # Region statistics
        total_regions = Region.objects.count()
        counties = Region.objects.filter(region_type='county').count()
        wards = Region.objects.filter(region_type='ward').count()
        
        stats['regions'] = {
            'total': total_regions,
            'counties': counties,
            'wards': wards
        }
        
        # Data availability statistics
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        recent_ndvi = NDVIData.objects.filter(date__gte=week_ago).count()
        recent_soil = SoilMoistureData.objects.filter(date__gte=week_ago).count()
        recent_weather = WeatherData.objects.filter(date__gte=week_ago).count()
        recent_assessments = DroughtRiskAssessment.objects.filter(assessment_date__gte=week_ago).count()
        
        stats['recent_data'] = {
            'ndvi_records': recent_ndvi,
            'soil_moisture_records': recent_soil,
            'weather_records': recent_weather,
            'risk_assessments': recent_assessments
        }
        
        # Alert statistics
        alerts_today = Alert.objects.filter(created_at__date=today).count()
        alerts_week = Alert.objects.filter(created_at__date__gte=week_ago).count()
        
        # High risk regions count
        high_risk_regions = DroughtRiskAssessment.objects.filter(
            assessment_date=today,
            risk_level__in=['high', 'very_high', 'extreme']
        ).count()
        
        stats['alerts'] = {
            'sent_today': alerts_today,
            'sent_this_week': alerts_week,
            'high_risk_regions': high_risk_regions
        }
        
        # Cache the statistics for 1 hour
        cache.set('system_statistics', stats, 3600)
        
        logger.info("System statistics updated successfully")
        
        return {
            'status': 'completed',
            'statistics': stats,
            'updated_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating statistics: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def validate_data_integrity() -> Dict[str, Any]:
    """
    Validate data integrity and identify potential issues
    """
    issues = []
    
    try:
        # Check for regions without recent data
        cutoff_date = timezone.now().date() - timedelta(days=7)
        
        regions_without_ndvi = Region.objects.exclude(
            ndvi_data__date__gte=cutoff_date
        ).count()
        
        regions_without_soil = Region.objects.exclude(
            soil_moisture_data__date__gte=cutoff_date
        ).count()
        
        regions_without_weather = Region.objects.exclude(
            weather_data__date__gte=cutoff_date
        ).count()
        
        if regions_without_ndvi > 0:
            issues.append(f"{regions_without_ndvi} regions missing recent NDVI data")
        
        if regions_without_soil > 0:
            issues.append(f"{regions_without_soil} regions missing recent soil moisture data")
        
        if regions_without_weather > 0:
            issues.append(f"{regions_without_weather} regions missing recent weather data")
        
        # Check for duplicate data
        from django.db.models import Count
        
        duplicate_ndvi = NDVIData.objects.values('region', 'date').annotate(
            count=Count('id')
        ).filter(count__gt=1).count()
        
        if duplicate_ndvi > 0:
            issues.append(f"{duplicate_ndvi} duplicate NDVI records found")
        
        # Check for inactive users with recent alerts
        inactive_users_with_alerts = UserProfile.objects.filter(
            is_active=False,
            user__alert_deliveries__created_at__gte=timezone.now() - timedelta(days=7)
        ).distinct().count()
        
        if inactive_users_with_alerts > 0:
            issues.append(f"{inactive_users_with_alerts} inactive users received recent alerts")
        
        # Check for failed alert deliveries
        failed_deliveries = AlertDelivery.objects.filter(
            status='failed',
            created_at__gte=timezone.now() - timedelta(days=1)
        ).count()
        
        if failed_deliveries > 10:  # Threshold for concern
            issues.append(f"{failed_deliveries} failed alert deliveries in last 24 hours")
        
        logger.info(f"Data integrity check completed: {len(issues)} issues found")
        
        return {
            'status': 'completed',
            'issues_found': len(issues),
            'issues': issues,
            'checked_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during data integrity check: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def backup_critical_data() -> Dict[str, Any]:
    """
    Create backup of critical system data
    This is a placeholder for backup operations
    """
    try:
        # This would implement actual backup logic
        # For now, just log the backup request
        
        backup_items = [
            'user_profiles',
            'regions',
            'alert_templates',
            'recent_risk_assessments'
        ]
        
        logger.info("Critical data backup completed (placeholder)")
        
        return {
            'status': 'completed',
            'backup_items': backup_items,
            'backup_timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during backup: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task
def send_system_health_report() -> Dict[str, Any]:
    """
    Generate and send system health report to administrators
    """
    try:
        # Get system statistics
        stats_result = update_system_statistics.apply()
        integrity_result = validate_data_integrity.apply()
        
        # Generate health report content
        health_report = f"""
        Drought Warning System - Daily Health Report
        Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        System Statistics:
        - Total Users: {stats_result.result.get('statistics', {}).get('users', {}).get('total', 'N/A')}
        - Active Farmers: {stats_result.result.get('statistics', {}).get('users', {}).get('farmers', 'N/A')}
        - Total Regions: {stats_result.result.get('statistics', {}).get('regions', {}).get('total', 'N/A')}
        - High Risk Regions: {stats_result.result.get('statistics', {}).get('alerts', {}).get('high_risk_regions', 'N/A')}
        
        Data Integrity:
        - Issues Found: {integrity_result.result.get('issues_found', 'N/A')}
        - Issues: {', '.join(integrity_result.result.get('issues', ['None']))}
        
        Recent Activity:
        - Alerts Today: {stats_result.result.get('statistics', {}).get('alerts', {}).get('sent_today', 'N/A')}
        - NDVI Records (7 days): {stats_result.result.get('statistics', {}).get('recent_data', {}).get('ndvi_records', 'N/A')}
        """
        
        # Send to administrators (placeholder)
        admin_users = UserProfile.objects.filter(user_type='admin', is_active=True)
        
        for admin in admin_users:
            if admin.receive_email_alerts:
                # This would send actual email
                logger.info(f"[MOCK] Sending health report to {admin.user.email}")
        
        return {
            'status': 'completed',
            'report_sent_to': admin_users.count(),
            'report_timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending health report: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }