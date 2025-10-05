import json
import uuid
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from .models import USSDSession, USSDUser
from core.models import Region
from drought_data.models import WeatherData
from alerts.models import Alert
from farmers.models import FarmerProfile


class USSDHandler:
    """Main USSD request handler"""
    
    def __init__(self):
        self.menu_handlers = {
            'main_menu': self.handle_main_menu,
            'weather_info': self.handle_weather_info,
            'drought_alerts': self.handle_drought_alerts,
            'crop_advice': self.handle_crop_advice,
            'registration': self.handle_registration,
            'profile_update': self.handle_profile_update,
            'help': self.handle_help,
        }
    
    def process_request(self, session_id, service_code, phone_number, text=""):
        """Process USSD request and return response"""
        
        # Get or create session
        session, created = USSDSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'phone_number': phone_number,
                'current_state': 'main_menu',
                'context_data': {}
            }
        )
        
        if not created:
            session.update_activity()
        
        # Clean old sessions
        self._cleanup_old_sessions()
        
        # Process based on current state and input
        if text == "":
            # Initial request - show main menu
            response = self.handle_main_menu(session, "")
        else:
            # Handle based on current state
            handler = self.menu_handlers.get(session.current_state, self.handle_main_menu)
            response = handler(session, text)
        
        return response
    
    def handle_main_menu(self, session, text):
        """Handle main menu navigation"""
        
        if text == "":
            # Show main menu
            session.current_state = 'main_menu'
            session.save()
            
            menu = "CON Welcome to Drought Alert System\n"
            menu += "1. Weather Information\n"
            menu += "2. Drought Alerts\n"
            menu += "3. Crop Advice\n"
            menu += "4. Register/Update Profile\n"
            menu += "5. Help"
            return menu
        
        # Handle menu selection
        choice = text.strip()
        
        if choice == "1":
            session.current_state = 'weather_info'
            session.save()
            return self.handle_weather_info(session, "")
        elif choice == "2":
            session.current_state = 'drought_alerts'
            session.save()
            return self.handle_drought_alerts(session, "")
        elif choice == "3":
            session.current_state = 'crop_advice'
            session.save()
            return self.handle_crop_advice(session, "")
        elif choice == "4":
            session.current_state = 'registration'
            session.save()
            return self.handle_registration(session, "")
        elif choice == "5":
            session.current_state = 'help'
            session.save()
            return self.handle_help(session, "")
        else:
            return "CON Invalid option. Please try again.\n0. Back to main menu"
    
    def handle_weather_info(self, session, text):
        """Handle weather information requests"""
        
        if text in ["", "1"]:  # Initial request or selected weather
            # Get recent weather data
            recent_weather = WeatherData.objects.filter(
                region__isnull=False
            ).order_by('-date')[:5]
            
            if recent_weather:
                response = "CON Latest Weather Info:\n"
                for weather in recent_weather:
                    response += f"{weather.region.name}: {weather.temperature_avg}°C, "
                    response += f"{weather.humidity_percent}% humidity\n"
                response += "\n0. Back to main menu"
            else:
                response = "CON No weather data available.\n0. Back to main menu"
            
            return response
        
        elif text == "0":
            # Back to main menu
            session.current_state = 'main_menu'
            session.save()
            return self.handle_main_menu(session, "")
        
        return "CON Invalid option.\n0. Back to main menu"
    
    def handle_drought_alerts(self, session, text):
        """Handle drought alerts"""
        
        if text in ["", "2"]:  # Initial request or selected alerts
            # Get recent drought alerts
            recent_alerts = Alert.objects.filter(
                status="sent"
            ).order_by('-created_at')[:3]
            
            if recent_alerts:
                response = "CON Active Drought Alerts:\n"
                for alert in recent_alerts:
                    response += f"• {alert.region.name}: {alert.priority} risk\n"
                    response += f"  {alert.message[:50]}...\n"
                response += "\n0. Back to main menu"
            else:
                response = "CON No active drought alerts.\n0. Back to main menu"
            
            return response
        
        elif text == "0":
            # Back to main menu
            session.current_state = 'main_menu'
            session.save()
            return self.handle_main_menu(session, "")
        
        return "CON Invalid option.\n0. Back to main menu"
    
    def handle_crop_advice(self, session, text):
        """Handle crop advice requests"""
        
        if text in ["", "3"]:  # Initial request or selected crop advice
            response = "CON Crop Advice:\n"
            response += "1. Drought-resistant crops\n"
            response += "2. Water conservation tips\n"
            response += "3. Planting calendar\n"
            response += "0. Back to main menu"
            return response
        
        elif text in ["1", "3*1"]:
            response = "END Drought-resistant crops:\n"
            response += "• Sorghum - very drought tolerant\n"
            response += "• Pearl millet - good for dry areas\n"
            response += "• Cowpeas - nitrogen fixing\n"
            response += "• Cassava - deep root system\n"
            response += "\nContact extension officer for seeds."
            session.end_session()
            return response
        
        elif text in ["2", "3*2"]:
            response = "END Water conservation tips:\n"
            response += "• Mulch around plants\n"
            response += "• Use drip irrigation\n"
            response += "• Plant cover crops\n"
            response += "• Harvest rainwater\n"
            response += "\nSave water, save crops!"
            session.end_session()
            return response
        
        elif text in ["3", "3*3"]:
            response = "END Planting Calendar:\n"
            response += "• March-May: Short rains crops\n"
            response += "• October-December: Long rains crops\n"
            response += "• Check local weather before planting\n"
            response += "\nTiming is everything!"
            session.end_session()
            return response
        
        elif text == "0":
            session.current_state = 'main_menu'
            session.save()
            return self.handle_main_menu(session, "")
        
        return "CON Invalid option.\n0. Back to main menu"
    
    def handle_registration(self, session, text):
        """Handle user registration/profile update"""
        
        context = session.context_data
        
        if text in ["", "4"]:  # Initial registration
            context['step'] = 'name'
            session.context_data = context
            session.save()
            return "CON Enter your full name:"
        
        elif context.get('step') == 'name':
            # Save name and ask for region
            context['name'] = text.strip()
            context['step'] = 'region'
            session.context_data = context
            session.save()
            
            regions = Region.objects.all()[:5]  # Show first 5 regions
            response = "CON Select your region:\n"
            for i, region in enumerate(regions, 1):
                response += f"{i}. {region.name}\n"
            return response
        
        elif context.get('step') == 'region':
            # Save region and ask for farm size
            try:
                region_index = int(text) - 1
                regions = list(Region.objects.all()[:5])
                if 0 <= region_index < len(regions):
                    context['region'] = regions[region_index].id
                    context['step'] = 'farm_size'
                    session.context_data = context
                    session.save()
                    return "CON Enter farm size in acres:"
                else:
                    return "CON Invalid region. Enter number 1-5:"
            except ValueError:
                return "CON Enter a valid number:"
        
        elif context.get('step') == 'farm_size':
            # Save farm size and ask for crops
            try:
                context['farm_size'] = float(text)
                context['step'] = 'crops'
                session.context_data = context
                session.save()
                return "CON Enter main crops (e.g., maize, beans):"
            except ValueError:
                return "CON Enter a valid number for farm size:"
        
        elif context.get('step') == 'crops':
            # Complete registration
            context['crops'] = text.strip()
            
            # Create or update USSD user
            ussd_user, created = USSDUser.objects.get_or_create(
                phone_number=session.phone_number,
                defaults={
                    'full_name': context['name'],
                    'region_id': context['region'],
                    'farm_size_acres': context['farm_size'],
                    'primary_crops': context['crops'],
                }
            )
            
            if not created:
                # Update existing user
                ussd_user.full_name = context['name']
                ussd_user.region_id = context['region']
                ussd_user.farm_size_acres = context['farm_size']
                ussd_user.primary_crops = context['crops']
                ussd_user.save()
            
            # Clear context and end session
            session.context_data = {}
            session.end_session()
            
            response = f"END Registration successful!\n"
            response += f"Name: {context['name']}\n"
            response += f"Farm: {context['farm_size']} acres\n"
            response += f"Crops: {context['crops']}\n"
            response += f"You will receive drought alerts."
            
            return response
        
        return "CON Something went wrong. Try again."
    
    def handle_profile_update(self, session, text):
        """Handle profile updates"""
        return self.handle_registration(session, text)
    
    def handle_help(self, session, text):
        """Handle help requests"""
        
        if text in ["", "5"]:
            response = "END USSD Drought Alert Help:\n\n"
            response += "This service provides:\n"
            response += "• Real-time weather updates\n"
            response += "• Drought risk alerts\n"
            response += "• Crop advice & tips\n"
            response += "• Free registration\n\n"
            response += "Available 24/7\n"
            response += "No internet required\n"
            response += "Works on any phone"
            
            session.end_session()
            return response
        
        return "END Help information displayed."
    
    def _cleanup_old_sessions(self):
        """Clean up old inactive sessions"""
        cutoff_time = timezone.now() - timedelta(hours=1)
        USSDSession.objects.filter(
            last_activity__lt=cutoff_time,
            is_active=True
        ).update(is_active=False, current_state='ended')
