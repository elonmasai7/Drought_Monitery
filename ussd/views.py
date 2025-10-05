import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
from .services import USSDHandler

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class USSDCallbackView(View):
    """Handle USSD callbacks from Africa's Talking or other providers"""
    
    def post(self, request):
        """Process USSD POST request"""
        
        # Get parameters (Africa's Talking format)
        session_id = request.POST.get('sessionId', '')
        service_code = request.POST.get('serviceCode', '')
        phone_number = request.POST.get('phoneNumber', '')
        text = request.POST.get('text', '')
        
        # Log the request
        logger.info(f"USSD Request - SessionID: {session_id}, Phone: {phone_number}, Text: '{text}'")
        
        try:
            # Process the USSD request
            handler = USSDHandler()
            response = handler.process_request(session_id, service_code, phone_number, text)
            
            # Log the response
            logger.info(f"USSD Response - SessionID: {session_id}, Response: '{response[:100]}...'")
            
            return HttpResponse(response, content_type='text/plain')
            
        except Exception as e:
            logger.error(f"USSD Error - SessionID: {session_id}, Error: {str(e)}")
            return HttpResponse("END Service temporarily unavailable. Please try again later.", 
                              content_type='text/plain')


@method_decorator(csrf_exempt, name='dispatch') 
class TwilioUSSDView(View):
    """Handle USSD callbacks from Twilio"""
    
    def post(self, request):
        """Process Twilio USSD POST request"""
        
        # Get parameters (Twilio format)
        session_id = request.POST.get('From', '') + '_' + request.POST.get('To', '')
        service_code = request.POST.get('To', '')
        phone_number = request.POST.get('From', '')
        text = request.POST.get('Body', '')
        
        # Log the request
        logger.info(f"Twilio USSD Request - Phone: {phone_number}, Text: '{text}'")
        
        try:
            # Process the USSD request
            handler = USSDHandler()
            response = handler.process_request(session_id, service_code, phone_number, text)
            
            # Convert to TwiML format
            twiml_response = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{response}</Message></Response>'
            
            logger.info(f"Twilio USSD Response - Phone: {phone_number}, Response sent")
            
            return HttpResponse(twiml_response, content_type='text/xml')
            
        except Exception as e:
            logger.error(f"Twilio USSD Error - Phone: {phone_number}, Error: {str(e)}")
            error_twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Message>END Service temporarily unavailable.</Message></Response>'
            return HttpResponse(error_twiml, content_type='text/xml')


# Legacy function-based views for backward compatibility
@csrf_exempt
@require_POST
def ussd_callback(request):
    """Legacy function-based view for USSD callbacks"""
    view = USSDCallbackView()
    return view.post(request)


@csrf_exempt
@require_POST  
def twilio_ussd_callback(request):
    """Legacy function-based view for Twilio USSD callbacks"""
    view = TwilioUSSDView()
    return view.post(request)
