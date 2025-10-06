#!/usr/bin/env python
"""
Test the improved signup flow to verify it redirects properly with valid data.
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

def test_improved_signup():
    print("🚀 Testing Improved Signup Flow")
    print("=" * 50)
    
    client = Client(HTTP_HOST='localhost')
    
    # Clean up any existing test user
    User.objects.filter(username='improvedtest').delete()
    
    print("\n📝 Testing valid signup data...")
    valid_signup_data = {
        'username': 'improvedtest',
        'email': 'improved@example.com', 
        'password1': 'StrongPass123!',  # Meets all Django requirements
        'password2': 'StrongPass123!'   # Matches password1
    }
    
    response = client.post(reverse('signup'), valid_signup_data, follow=True)
    
    print(f"Response status: {response.status_code}")
    print(f"Final URL: {response.request['PATH_INFO']}")
    print(f"✅ Redirected to grants: {'/grants/apply/' in response.request['PATH_INFO']}")
    
    # Verify user was created and logged in
    user_exists = User.objects.filter(username='improvedtest').exists()
    print(f"✅ User created: {user_exists}")
    
    # Check if user is logged in by looking for grants application page content
    content = response.content.decode()
    print(f"✅ Grants page loaded: {'Grant Application' in content or 'Apply for Grant' in content}")
    
    # Test invalid data (should stay on signup page with errors)
    print("\n❌ Testing invalid signup data (weak password)...")
    User.objects.filter(username='weaktest').delete()
    
    weak_signup_data = {
        'username': 'weaktest',
        'email': 'weak@example.com',
        'password1': '123',      # Too weak
        'password2': '123'       # Too weak
    }
    
    response = client.post(reverse('signup'), weak_signup_data)
    print(f"Response status: {response.status_code}")
    print(f"Stays on signup page: {response.status_code == 200}")
    
    content = response.content.decode()
    print(f"✅ Shows validation errors: {'Please fix the following errors' in content}")
    print(f"✅ Shows password requirements: {'Password requirements' in content}")

if __name__ == "__main__":
    test_improved_signup()