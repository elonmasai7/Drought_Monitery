from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any

from .models import Alert, AlertDelivery, AlertTemplate, AlertSubscription
from .services import whatsapp_service, sms_service, email_service
from core.models import UserProfile, Region
from drought_data.models import DroughtRiskAssessment
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


@shared_task
def send_alert(alert_id: int) -> Dict[str, Any]:
    """
    Send an alert to all targeted recipients
    """
    try:
        alert = Alert.objects.get(id=alert_id)
        
        if alert.status != 'sending':
            alert.status = 'sending'
            alert.save()
        
        # Determine target users
        target_users = []
        
        if alert.target_users.exists():
            # Specific users targeted
            target_users = list(alert.target_users.all())
        else:
            # All users in the region
            target_users = list(UserProfile.objects.filter(
                region=alert.region,
                is_active=True
            ))
        
        alert.total_recipients = len(target_users)
        alert.save()
        
        # Create delivery records and send
        successful_sends = 0
        failed_sends = 0
        
        for user_profile in target_users:
            # Check user subscriptions
            if not _should_send_alert_to_user(alert, user_profile):
                continue
            
            # Determine delivery methods based on user preferences
            delivery_methods = _get_user_delivery_methods(user_profile)
            
            for method in delivery_methods:
                try:
                    delivery = AlertDelivery.objects.create(
                        alert=alert,
                        recipient=user_profile,
                        delivery_method=method,
                        phone_number=user_profile.phone_number if method in ['whatsapp', 'sms'] else '',
                        email_address=user_profile.user.email if method == 'email' else ''
                    )
                    
                    # Send the actual message
                    send_result = _send_message_via_method(delivery, method)
                    
                    if send_result['success']:
                        delivery.status = 'sent'
                        delivery.sent_at = timezone.now()
                        delivery.external_message_id = send_result.get('message_id', '')
                        successful_sends += 1
                    else:
                        delivery.status = 'failed'
                        delivery.error_message = send_result.get('error', 'Unknown error')
                        failed_sends += 1
                    
                    delivery.save()
                    
                except Exception as e:
                    logger.error(f"Error creating delivery for user {user_profile.id}: {str(e)}")
                    failed_sends += 1
        
        # Update alert status
        alert.successfully_sent = successful_sends
        alert.failed_sends = failed_sends
        alert.status = 'sent'
        alert.sent_at = timezone.now()
        alert.save()
        
        logger.info(f"Alert {alert.alert_id} sent: {successful_sends} successful, {failed_sends} failed")
        
        return {
            'status': 'completed',
            'alert_id': alert.alert_id,
            'total_recipients': alert.total_recipients,
            'successful_sends': successful_sends,
            'failed_sends': failed_sends
        }
        
    except Alert.DoesNotExist:
        logger.error(f"Alert with ID {alert_id} not found")
        return {'status': 'error', 'message': 'Alert not found'}
    except Exception as e:
        logger.error(f"Error sending alert {alert_id}: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def process_scheduled_alerts() -> Dict[str, Any]:
    """
    Process alerts that are scheduled to be sent
    """
    now = timezone.now()
    
    # Find alerts that should be sent now
    scheduled_alerts = Alert.objects.filter(
        status='scheduled',
        scheduled_send_time__lte=now
    )
    
    processed_count = 0
    
    for alert in scheduled_alerts:
        try:
            # Trigger the send_alert task
            send_alert.delay(alert.id)
            processed_count += 1
            logger.info(f"Triggered sending for scheduled alert {alert.alert_id}")
        except Exception as e:
            logger.error(f"Error processing scheduled alert {alert.alert_id}: {str(e)}")
    
    return {
        'status': 'completed',
        'processed_alerts': processed_count
    }


@shared_task
def check_and_send_automated_alerts() -> Dict[str, Any]:
    """
    Check drought risk levels and send automated alerts based on thresholds
    """
    results = {
        'alerts_created': 0,
        'alerts_sent': 0,
        'regions_checked': 0
    }
    
    # Get active alert templates that have auto-send enabled
    auto_templates = AlertTemplate.objects.filter(
        is_active=True,
        auto_send=True,
        trigger_risk_threshold__isnull=False
    )
    
    if not auto_templates.exists():
        logger.info("No auto-send templates configured")
        return results
    
    # Check recent risk assessments
    today = timezone.now().date()
    recent_assessments = DroughtRiskAssessment.objects.filter(
        assessment_date=today
    )
    
    results['regions_checked'] = recent_assessments.count()
    
    for assessment in recent_assessments:
        for template in auto_templates:
            # Check if risk score exceeds threshold
            if assessment.risk_score >= template.trigger_risk_threshold:
                
                # Check if we already sent this type of alert today for this region
                existing_alert = Alert.objects.filter(
                    region=assessment.region,
                    template=template,
                    created_at__date=today
                ).first()
                
                if existing_alert:
                    continue  # Already sent today
                
                # Create and send alert
                try:
                    alert = _create_automated_alert(template, assessment)
                    results['alerts_created'] += 1
                    
                    # Send immediately
                    send_alert.delay(alert.id)
                    results['alerts_sent'] += 1
                    
                    logger.info(f"Created automated alert for {assessment.region.name} with risk {assessment.risk_score}")
                    
                except Exception as e:
                    logger.error(f"Error creating automated alert: {str(e)}")
    
    return results


@shared_task
def retry_failed_deliveries() -> Dict[str, Any]:
    """
    Retry failed alert deliveries
    """
    # Find failed deliveries that haven't exceeded max retries
    failed_deliveries = AlertDelivery.objects.filter(
        status='failed',
        retry_count__lt=models.F('max_retries')
    )
    
    retried_count = 0
    success_count = 0
    
    for delivery in failed_deliveries:
        try:
            # Increment retry count
            delivery.retry_count += 1
            
            # Attempt to resend
            send_result = _send_message_via_method(delivery, delivery.delivery_method)
            
            if send_result['success']:
                delivery.status = 'sent'
                delivery.sent_at = timezone.now()
                delivery.external_message_id = send_result.get('message_id', '')
                delivery.error_message = ''
                success_count += 1
            else:
                delivery.error_message = send_result.get('error', 'Retry failed')
            
            delivery.save()
            retried_count += 1
            
        except Exception as e:
            logger.error(f"Error retrying delivery {delivery.id}: {str(e)}")
    
    return {
        'status': 'completed',
        'retried_deliveries': retried_count,
        'successful_retries': success_count
    }


@shared_task
def update_delivery_status_from_webhooks():
    """
    Update delivery status based on webhook data from external services
    This would be called when receiving delivery confirmations from Twilio, etc.
    """
    # This is a placeholder for webhook processing
    # In real implementation, this would process webhook data to update delivery statuses
    pass


# Helper functions
def _should_send_alert_to_user(alert: Alert, user_profile: UserProfile) -> bool:
    """
    Check if alert should be sent to a specific user based on subscriptions
    """
    try:
        subscription = AlertSubscription.objects.get(
            user_profile=user_profile,
            alert_type=alert.template.alert_type
        )
        
        if not subscription.is_subscribed:
            return False
        
        # Check severity level
        severity_levels = ['info', 'low', 'moderate', 'high', 'critical', 'emergency']
        alert_severity_index = severity_levels.index(alert.template.severity_level)
        min_severity_index = severity_levels.index(subscription.min_severity_level)
        
        return alert_severity_index >= min_severity_index
        
    except AlertSubscription.DoesNotExist:
        # If no subscription exists, default to sending moderate and above
        severity_levels = ['info', 'low', 'moderate', 'high', 'critical', 'emergency']
        alert_severity_index = severity_levels.index(alert.template.severity_level)
        return alert_severity_index >= 2  # moderate and above


def _get_user_delivery_methods(user_profile: UserProfile) -> List[str]:
    """
    Get preferred delivery methods for a user
    """
    methods = []
    
    if user_profile.receive_whatsapp_alerts:
        methods.append('whatsapp')
    
    if user_profile.receive_sms_alerts:
        methods.append('sms')
    
    if user_profile.receive_email_alerts:
        methods.append('email')
    
    # Default to SMS if no preferences set
    if not methods:
        methods.append('sms')
    
    return methods


def _send_message_via_method(delivery: AlertDelivery, method: str) -> Dict[str, Any]:
    """
    Send message via specific delivery method
    This is a placeholder that would integrate with real services
    """
    try:
        alert = delivery.alert
        
        if method == 'whatsapp':
            return _send_whatsapp_message(
                delivery.phone_number,
                alert.message,
                alert.title
            )
        elif method == 'sms':
            return _send_sms_message(
                delivery.phone_number,
                alert.sms_message or alert.message[:160]
            )
        elif method == 'email':
            return _send_email_message(
                delivery.email_address,
                alert.title,
                alert.message
            )
        else:
            return {'success': False, 'error': f'Unknown delivery method: {method}'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _send_whatsapp_message(phone_number: str, message: str, title: str) -> Dict[str, Any]:
    """
    Send WhatsApp message via Twilio API
    """
    return whatsapp_service.send_message(phone_number, message, title)


def _send_sms_message(phone_number: str, message: str) -> Dict[str, Any]:
    """
    Send SMS message via Twilio or Africa's Talking API
    """
    return sms_service.send_message(phone_number, message)


def _send_email_message(email: str, subject: str, message: str) -> Dict[str, Any]:
    """
    Send email message via Django email backend
    """
    return email_service.send_message(email, subject, message)


def _create_automated_alert(template: AlertTemplate, assessment: DroughtRiskAssessment) -> Alert:
    """
    Create an automated alert based on template and risk assessment
    """
    from django.contrib.auth.models import User
    
    # Get system user for automated alerts
    system_user, created = User.objects.get_or_create(
        username='system',
        defaults={
            'email': 'system@droughtwarning.com',
            'first_name': 'System',
            'last_name': 'Automated'
        }
    )
    
    # Generate alert content
    context = {
        'region_name': assessment.region.name,
        'risk_level': assessment.get_risk_level_display(),
        'risk_score': assessment.risk_score,
        'assessment_date': assessment.assessment_date,
        'recommendations': assessment.recommended_actions
    }
    
    title = template.title_template.format(**context)
    message = template.message_template.format(**context)
    sms_message = template.sms_template.format(**context)
    
    alert = Alert.objects.create(
        template=template,
        region=assessment.region,
        title=title,
        message=message,
        sms_message=sms_message,
        priority='high' if assessment.risk_score >= 70 else 'normal',
        status='sending',
        drought_assessment=assessment,
        created_by=system_user
    )
    
    return alert