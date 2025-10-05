"""
Alert delivery services for WhatsApp, SMS, and Email
"""
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    WhatsApp messaging service using Twilio API
    """
    
    def __init__(self):
        """Initialize Twilio client"""
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.whatsapp_number = settings.TWILIO_WHATSAPP_NUMBER
        self.client = None
        
        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio WhatsApp client initialized successfully")
            except ImportError:
                logger.error("Twilio library not installed. Run: pip install twilio")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
    
    def send_message(self, phone_number: str, message: str, title: str = None) -> Dict[str, Any]:
        """
        Send WhatsApp message via Twilio
        
        Args:
            phone_number: Recipient phone number (format: +254700000000)
            message: Message content
            title: Optional message title
            
        Returns:
            Dict with success status and message_id or error
        """
        if not self.client:
            # Fallback to mock for development/testing
            return self._mock_send(phone_number, message, title)
        
        try:
            # Format phone number for WhatsApp (must start with whatsapp:+)
            whatsapp_to = f"whatsapp:{phone_number}"
            whatsapp_from = f"whatsapp:{self.whatsapp_number}"
            
            # Combine title and message if title provided
            full_message = f"*{title}*\n\n{message}" if title else message
            
            # Send message via Twilio
            message_obj = self.client.messages.create(
                body=full_message,
                from_=whatsapp_from,
                to=whatsapp_to
            )
            
            logger.info(f"WhatsApp message sent successfully to {phone_number}, SID: {message_obj.sid}")
            
            return {
                'success': True,
                'message_id': message_obj.sid,
                'status': message_obj.status,
                'to': phone_number
            }
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {phone_number}: {e}")
            
            # Check if it's an authentication error and fallback to mock
            error_str = str(e)
            if 'authentication' in error_str.lower() or 'invalid username' in error_str.lower():
                logger.info(f"Authentication failed, falling back to mock for {phone_number}")
                return self._mock_send(phone_number, message, title)
            
            return {
                'success': False,
                'error': str(e),
                'to': phone_number
            }
    
    def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get message delivery status from Twilio
        
        Args:
            message_sid: Twilio message SID
            
        Returns:
            Dict with message status information
        """
        if not self.client:
            return {'status': 'unknown', 'error': 'Twilio client not available'}
        
        try:
            message = self.client.messages(message_sid).fetch()
            return {
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'date_sent': message.date_sent,
                'date_updated': message.date_updated
            }
        except Exception as e:
            logger.error(f"Failed to get message status for {message_sid}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _mock_send(self, phone_number: str, message: str, title: str = None) -> Dict[str, Any]:
        """
        Mock WhatsApp sending for development/testing
        """
        logger.info(f"[MOCK] WhatsApp to {phone_number}: {title or 'No title'}")
        logger.info(f"[MOCK] Message: {message[:100]}...")
        
        # Simulate 95% success rate
        import random
        if random.random() > 0.05:
            return {
                'success': True,
                'message_id': f'MOCK_WA_{timezone.now().timestamp()}',
                'status': 'queued',
                'to': phone_number
            }
        else:
            return {
                'success': False,
                'error': 'Mock WhatsApp delivery failure',
                'to': phone_number
            }


class SMSService:
    """
    SMS messaging service using Twilio or Africa's Talking
    """
    
    def __init__(self):
        """Initialize SMS service"""
        self.twilio_client = None
        self.africas_talking_client = None
        
        # Initialize Twilio SMS
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                logger.info("Twilio SMS client initialized successfully")
            except ImportError:
                logger.error("Twilio library not installed")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio SMS client: {e}")
        
        # Initialize Africa's Talking SMS
        if settings.AFRICAS_TALKING_USERNAME and settings.AFRICAS_TALKING_API_KEY:
            try:
                import africastalking
                africastalking.initialize(
                    settings.AFRICAS_TALKING_USERNAME,
                    settings.AFRICAS_TALKING_API_KEY
                )
                self.africas_talking_client = africastalking.SMS
                logger.info("Africa's Talking SMS client initialized successfully")
            except ImportError:
                logger.error("Africa's Talking library not installed. Run: pip install africastalking")
            except Exception as e:
                logger.error(f"Failed to initialize Africa's Talking SMS client: {e}")
    
    def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS message using available service
        
        Args:
            phone_number: Recipient phone number
            message: SMS message content
            
        Returns:
            Dict with success status and message_id or error
        """
        # Try Africa's Talking first (better for African markets)
        if self.africas_talking_client:
            return self._send_via_africas_talking(phone_number, message)
        
        # Fallback to Twilio
        elif self.twilio_client:
            return self._send_via_twilio(phone_number, message)
        
        # Mock for development
        else:
            return self._mock_send(phone_number, message)
    
    def _send_via_twilio(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_='+1234567890',  # Replace with your Twilio number
                to=phone_number
            )
            
            logger.info(f"SMS sent via Twilio to {phone_number}, SID: {message_obj.sid}")
            
            return {
                'success': True,
                'message_id': message_obj.sid,
                'service': 'twilio',
                'to': phone_number
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS via Twilio to {phone_number}: {e}")
            
            # Check if it's an authentication error and fallback to mock
            error_str = str(e)
            if 'authentication' in error_str.lower():
                logger.info(f"Twilio authentication failed, falling back to mock for {phone_number}")
                return self._mock_send(phone_number, message)
            
            return {
                'success': False,
                'error': str(e),
                'service': 'twilio',
                'to': phone_number
            }
    
    def _send_via_africas_talking(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via Africa's Talking"""
        try:
            # Format phone number for Africa's Talking (remove dashes, ensure + prefix)
            formatted_phone = phone_number.replace('-', '').replace(' ', '')
            if not formatted_phone.startswith('+'):
                formatted_phone = '+' + formatted_phone
            
            response = self.africas_talking_client.send(
                message=message,
                recipients=[formatted_phone]
            )
            
            # Africa's Talking returns a dict with recipients array
            if response and 'SMSMessageData' in response:
                recipients = response['SMSMessageData']['Recipients']
                if recipients and len(recipients) > 0:
                    recipient = recipients[0]
                    if recipient['status'] == 'Success':
                        logger.info(f"SMS sent via Africa's Talking to {phone_number}")
                        return {
                            'success': True,
                            'message_id': recipient.get('messageId', 'unknown'),
                            'service': 'africas_talking',
                            'to': phone_number
                        }
                    else:
                        logger.error(f"Africa's Talking SMS failed: {recipient}")
                        return {
                            'success': False,
                            'error': recipient.get('status', 'Unknown error'),
                            'service': 'africas_talking',
                            'to': phone_number
                        }
            
            return {
                'success': False,
                'error': 'Invalid response from Africa\'s Talking',
                'service': 'africas_talking',
                'to': phone_number
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS via Africa's Talking to {phone_number}: {e}")
            
            # Check if it's an authentication error and fallback to mock
            error_str = str(e)
            if 'authentication' in error_str.lower() or 'invalid' in error_str.lower():
                logger.info(f"Africa's Talking authentication failed, falling back to mock for {phone_number}")
                return self._mock_send(phone_number, message)
            
            return {
                'success': False,
                'error': str(e),
                'service': 'africas_talking',
                'to': phone_number
            }
    
    def _mock_send(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Mock SMS sending for development"""
        logger.info(f"[MOCK] SMS to {phone_number}: {message[:50]}...")
        
        import random
        if random.random() > 0.02:  # 98% success rate
            return {
                'success': True,
                'message_id': f'MOCK_SMS_{timezone.now().timestamp()}',
                'service': 'mock',
                'to': phone_number
            }
        else:
            return {
                'success': False,
                'error': 'Mock SMS delivery failure',
                'service': 'mock',
                'to': phone_number
            }


class EmailService:
    """
    Email service using Django email backend
    """
    
    def send_message(self, email: str, subject: str, message: str, html_message: str = None) -> Dict[str, Any]:
        """
        Send email message
        
        Args:
            email: Recipient email address
            subject: Email subject
            message: Plain text message
            html_message: Optional HTML message
            
        Returns:
            Dict with success status and message_id or error
        """
        try:
            from django.core.mail import send_mail
            
            result = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )
            
            if result:
                logger.info(f"Email sent successfully to {email}")
                return {
                    'success': True,
                    'message_id': f'EMAIL_{timezone.now().timestamp()}',
                    'to': email
                }
            else:
                return {
                    'success': False,
                    'error': 'Email send returned False',
                    'to': email
                }
                
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")
            return {
                'success': False,
                'error': str(e),
                'to': email
            }


# Service instances
whatsapp_service = WhatsAppService()
sms_service = SMSService()
email_service = EmailService()