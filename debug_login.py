#!/usr/bin/env python3
"""
Debug script to test role-based login functionality
"""
import os
import sys
import django
import requests
import re

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drought_warning_system.settings')
sys.path.append('/home/runner/app')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile
from core.permissions import get_user_role

BASE_URL = 'http://localhost:8000'

def test_user_data():
    """Test if demo users exist and have correct data"""
    print("=== TESTING USER DATA ===")
    users = ['admin', 'farmer', 'officer']
    
    for username in users:
        try:
            user = User.objects.get(username=username)
            profile = getattr(user, 'userprofile', None)
            role = get_user_role(user)
            
            print(f"\n✓ User: {username}")
            print(f"  - Active: {user.is_active}")
            print(f"  - Staff: {user.is_staff}")
            print(f"  - Superuser: {user.is_superuser}")
            print(f"  - Role: {role}")
            if profile:
                print(f"  - Profile Type: {profile.user_type}")
            else:
                print("  - ❌ No UserProfile found")
                
        except User.DoesNotExist:
            print(f"❌ User {username} does not exist")

def test_login_page():
    """Test if login page loads correctly"""
    print("\n=== TESTING LOGIN PAGE ===")
    try:
        response = requests.get(f'{BASE_URL}/dashboard/login/')
        if response.status_code == 200:
            print("✓ Login page loads successfully")
            
            # Check for key elements
            if 'csrf' in response.text.lower():
                print("✓ CSRF token found in page")
            else:
                print("❌ CSRF token not found")
                
            if 'farmer' in response.text.lower() and 'admin' in response.text.lower():
                print("✓ Role selection found")
            else:
                print("❌ Role selection not found")
                
        else:
            print(f"❌ Login page returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error loading login page: {e}")

def test_login_process(username, password, role):
    """Test the complete login process"""
    print(f"\n=== TESTING LOGIN: {username} as {role} ===")
    
    session = requests.Session()
    
    try:
        # Get login page to extract CSRF token
        response = session.get(f'{BASE_URL}/dashboard/login/')
        
        if response.status_code != 200:
            print(f"❌ Failed to get login page: {response.status_code}")
            return False
            
        # Parse CSRF token using regex
        csrf_pattern = r'<input[^>]*name=["\']csrfmiddlewaretoken["\'][^>]*value=["\']([^"\']*)'
        csrf_match = re.search(csrf_pattern, response.text)
        
        if not csrf_match:
            print("❌ CSRF token not found in login page")
            return False
            
        csrf_value = csrf_match.group(1)
        print(f"✓ CSRF token extracted: {csrf_value[:20]}...")
        
        # Attempt login
        login_data = {
            'username': username,
            'password': password,
            'user_role': role,
            'csrfmiddlewaretoken': csrf_value
        }
        
        response = session.post(f'{BASE_URL}/dashboard/login/', data=login_data, allow_redirects=False)
        
        print(f"Login response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            redirect_url = response.headers.get('Location', '')
            print(f"✓ Redirected to: {redirect_url}")
            
            # Check if redirect is to login (failed) or dashboard (success)
            if 'login' in redirect_url:
                print("❌ Login failed - redirected back to login")
                # Try to get the page with error messages
                error_response = session.get(f'{BASE_URL}/dashboard/login/')
                if 'Invalid username or password' in error_response.text:
                    print("❌ Error: Invalid credentials")
                elif 'do not have' in error_response.text:
                    print("❌ Error: Role permission denied")
                return False
            else:
                print("✓ Login successful!")
                
                # Test accessing the redirected page
                final_response = session.get(f'{BASE_URL}{redirect_url}')
                if final_response.status_code == 200:
                    print("✓ Successfully accessed dashboard")
                    return True
                else:
                    print(f"❌ Failed to access dashboard: {final_response.status_code}")
                    return False
                    
        elif response.status_code == 200:
            print("❌ Login failed - no redirect (stayed on login page)")
            # Check for error messages
            if 'Invalid username or password' in response.text:
                print("❌ Error: Invalid credentials")
            elif 'do not have' in response.text:
                print("❌ Error: Role permission denied")
            return False
        else:
            print(f"❌ Unexpected response status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during login process: {e}")
        return False

def main():
    print("🔍 DROUGHT MONITORING SYSTEM - LOGIN DEBUG TOOL")
    print("=" * 60)
    
    # Test 1: User data
    test_user_data()
    
    # Test 2: Login page
    test_login_page()
    
    # Test 3: Login processes
    test_cases = [
        ('admin', 'admin123', 'admin'),
        ('farmer', 'farmer123', 'farmer'),
        ('officer', 'officer123', 'admin'),  # Extension officers use admin portal
    ]
    
    results = []
    for username, password, role in test_cases:
        result = test_login_process(username, password, role)
        results.append((username, role, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    for username, role, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{username:8} as {role:7}: {status}")
    
    successful_logins = sum(1 for _, _, success in results if success)
    print(f"\nTotal successful logins: {successful_logins}/{len(results)}")
    
    if successful_logins == len(results):
        print("🎉 All login tests passed! Your role-based authentication is working correctly.")
    else:
        print("⚠️  Some login tests failed. Check the error messages above for details.")

if __name__ == '__main__':
    main()