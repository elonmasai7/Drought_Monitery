from django.urls import path
from . import views

app_name = 'ussd'

urlpatterns = [
    # Africa's Talking USSD callback
    path('callback/', views.USSDCallbackView.as_view(), name='callback'),
    
    # Twilio USSD callback  
    path('twilio-callback/', views.TwilioUSSDView.as_view(), name='twilio_callback'),
    
    # Legacy function-based views (for backward compatibility)
    path('callback-legacy/', views.ussd_callback, name='callback_legacy'),
    path('twilio-callback-legacy/', views.twilio_ussd_callback, name='twilio_callback_legacy'),
]
