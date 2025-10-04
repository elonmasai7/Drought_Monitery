from django.core.management.base import BaseCommand
from alerts.services import whatsapp_service, sms_service, email_service
from core.models import UserProfile
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Test WhatsApp, SMS, and Email messaging services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            help='Phone number to test WhatsApp/SMS (format: +254700000000)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to test email service',
        )
        parser.add_argument(
            '--service',
            type=str,
            choices=['whatsapp', 'sms', 'email', 'all'],
            default='all',
            help='Which service to test',
        )

    def handle(self, *args, **options):
        phone_number = options.get('phone')
        email_address = options.get('email')
        service = options.get('service')
        
        # If no specific contact info provided, use farmer demo user
        if not phone_number and not email_address:
            try:
                farmer_user = User.objects.get(username='farmer')
                user_profile = UserProfile.objects.get(user=farmer_user)
                phone_number = user_profile.phone_number
                email_address = farmer_user.email
                self.stdout.write(f"Using farmer demo user: {phone_number}, {email_address}")
            except (User.DoesNotExist, UserProfile.DoesNotExist):
                self.stdout.write(
                    self.style.ERROR(
                        'No demo farmer user found. Please create demo users first or provide --phone and --email arguments.'
                    )
                )
                return
        
        # Test messages
        test_title = "Drought Warning Test"
        test_message = """🌱 DROUGHT WARNING SYSTEM TEST 🌱

This is a test message from the Farmer-Centric Drought & Water Stress Early Warning System.

⚠️ Current Status: Testing Alert Delivery
📍 Region: Central Kenya
🔗 Risk Level: Moderate

Recommended Actions:
• Implement water conservation measures
• Monitor crop conditions closely
• Consider adjusting planting schedules

This is an automated test message. Please ignore if received unexpectedly.

Stay safe and keep farming! 🚜"""
        
        test_sms = "DROUGHT ALERT TEST: This is a test SMS from the Drought Warning System. Water conservation recommended. Risk: Moderate. Reply STOP to unsubscribe."
        
        results = []
        
        # Test WhatsApp
        if service in ['whatsapp', 'all'] and phone_number:
            self.stdout.write("Testing WhatsApp service...")
            result = whatsapp_service.send_message(phone_number, test_message, test_title)
            results.append(('WhatsApp', result))
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ WhatsApp sent successfully to {phone_number}"
                        f"\nMessage ID: {result.get('message_id', 'N/A')}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ WhatsApp failed: {result.get('error', 'Unknown error')}"
                    )
                )
        
        # Test SMS
        if service in ['sms', 'all'] and phone_number:
            self.stdout.write("Testing SMS service...")
            result = sms_service.send_message(phone_number, test_sms)
            results.append(('SMS', result))
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ SMS sent successfully to {phone_number}"
                        f"\nMessage ID: {result.get('message_id', 'N/A')}"
                        f"\nService: {result.get('service', 'Unknown')}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ SMS failed: {result.get('error', 'Unknown error')}"
                    )
                )
        
        # Test Email
        if service in ['email', 'all'] and email_address:
            self.stdout.write("Testing Email service...")
            result = email_service.send_message(
                email_address, 
                test_title, 
                test_message
            )
            results.append(('Email', result))
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Email sent successfully to {email_address}"
                        f"\nMessage ID: {result.get('message_id', 'N/A')}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Email failed: {result.get('error', 'Unknown error')}"
                    )
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("TEST SUMMARY")
        self.stdout.write("="*50)
        
        success_count = sum(1 for _, result in results if result['success'])
        total_count = len(results)
        
        for service_name, result in results:
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            self.stdout.write(f"{service_name}: {status}")
            if not result['success']:
                self.stdout.write(f"  Error: {result.get('error', 'Unknown')}")
        
        self.stdout.write(f"\nOverall: {success_count}/{total_count} services working")
        
        if success_count == total_count:
            self.stdout.write(self.style.SUCCESS("🎉 All messaging services are working correctly!"))
        else:
            self.stdout.write(self.style.WARNING("⚠️  Some messaging services need attention."))
            
        self.stdout.write("\nNote: If using mock services, this indicates the integration layer is working.")
        self.stdout.write("Configure API keys in settings to test actual delivery.")