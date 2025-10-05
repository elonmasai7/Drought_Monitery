from django.core.management.base import BaseCommand
from ussd.services import USSDHandler


class Command(BaseCommand):
    help = 'Test USSD service functionality'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing USSD Service...'))
        
        handler = USSDHandler()
        test_phone = "+254700000000"
        test_session = "test_session_123"
        
        # Test main menu
        self.stdout.write("\n=== Testing Main Menu ===")
        response = handler.process_request(test_session, "*384*1#", test_phone, "")
        self.stdout.write(f"Main Menu Response:\n{response}")
        
        # Test weather info
        self.stdout.write("\n=== Testing Weather Info ===")
        response = handler.process_request(test_session, "*384*1#", test_phone, "1")
        self.stdout.write(f"Weather Info Response:\n{response}")
        
        # Test drought alerts  
        self.stdout.write("\n=== Testing Drought Alerts ===")
        response = handler.process_request(test_session, "*384*1#", test_phone, "2")
        self.stdout.write(f"Drought Alerts Response:\n{response}")
        
        # Test crop advice
        self.stdout.write("\n=== Testing Crop Advice ===")
        response = handler.process_request(test_session, "*384*1#", test_phone, "3")
        self.stdout.write(f"Crop Advice Response:\n{response}")
        
        # Test registration
        self.stdout.write("\n=== Testing Registration ===")
        response = handler.process_request(test_session, "*384*1#", test_phone, "4")
        self.stdout.write(f"Registration Response:\n{response}")
        
        # Test help
        self.stdout.write("\n=== Testing Help ===")
        response = handler.process_request(test_session, "*384*1#", test_phone, "5")
        self.stdout.write(f"Help Response:\n{response}")
        
        self.stdout.write(self.style.SUCCESS('\nUSSD Service test completed successfully!'))
