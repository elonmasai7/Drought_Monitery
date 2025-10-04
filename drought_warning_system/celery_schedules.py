from celery.schedules import crontab

# Celery Beat periodic tasks configuration
CELERY_BEAT_SCHEDULE = {
    # Fetch data daily at 6 AM
    'fetch-daily-data': {
        'task': 'drought_data.tasks.fetch_all_data_for_all_regions',
        'schedule': crontab(hour=6, minute=0),  # 6:00 AM daily
        'args': (),
    },
    
    # Calculate drought risk daily at 7 AM (after data fetch) - NEW AUTOMATED TASK
    'calculate-daily-drought-risk': {
        'task': 'drought_data.automated_tasks.calculate_daily_drought_risk',
        'schedule': crontab(hour=7, minute=0),  # 7:00 AM daily
        'args': (),
    },
    
    # Trigger drought alerts daily at 7:30 AM (after risk calculation) - NEW AUTOMATED TASK
    'trigger-drought-alerts': {
        'task': 'drought_data.automated_tasks.trigger_drought_alerts',
        'schedule': crontab(hour=7, minute=30),  # 7:30 AM daily
        'args': (50.0,),  # Minimum risk threshold of 50.0
    },
    
    # Check for critical alerts every 2 hours during day
    'check-critical-alerts': {
        'task': 'drought_data.automated_tasks.trigger_drought_alerts',
        'schedule': crontab(hour='8-18/2', minute=0),  # Every 2 hours from 8 AM to 6 PM
        'args': (80.0,),  # Higher threshold for critical alerts
    },
    
    # Check for scheduled alerts every 15 minutes
    'process-scheduled-alerts': {
        'task': 'alerts.tasks.process_scheduled_alerts',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    
    # Check for automated alerts based on risk thresholds every hour
    'check-automated-alerts': {
        'task': 'alerts.tasks.check_and_send_automated_alerts',
        'schedule': crontab(minute=30),  # Every hour at 30 minutes past
    },
    
    # Retry failed deliveries every 2 hours
    'retry-failed-deliveries': {
        'task': 'alerts.tasks.retry_failed_deliveries',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
    },
    
    # Clean up old data weekly
    'cleanup-old-data': {
        'task': 'core.tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Monday 2 AM
        'args': (90,),  # Keep 90 days of data
    },
    
    # Generate daily reports at 8 PM
    'generate-daily-reports': {
        'task': 'dashboard.tasks.generate_daily_reports',
        'schedule': crontab(hour=20, minute=0),  # 8:00 PM daily
    },
    
    # Update user statistics daily at midnight
    'update-statistics': {
        'task': 'core.tasks.update_system_statistics',
        'schedule': crontab(hour=0, minute=30),  # 12:30 AM daily
    },
    
    # Recalculate risk for specific regions if triggered by external events
    'emergency-risk-calculation': {
        'task': 'drought_data.automated_tasks.calculate_daily_drought_risk',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes (can be triggered manually)
        'options': {'expires': 1800},  # Task expires after 30 minutes if not executed
        'args': (),
    },
}
