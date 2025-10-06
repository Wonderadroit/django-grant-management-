#!/usr/bin/env python
"""
Test authentication flow to ensure signup and login redirect properly.
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

def test_auth_flow():
    print("🔐 Testing Authentication Flow")
    print("=" * 50)
    
    client = Client(HTTP_HOST='localhost')
    
    # Test 1: Check that signup redirects to grants application
    print("\n📝 Test 1: Signup Flow")
    signup_data = {
        'username': 'testuser123',
        'email': 'test@example.com',
        'password1': 'testpass123!',
        'password2': 'testpass123!'
    }
    
    response = client.post(reverse('signup'), signup_data, follow=True)
    print(f"Signup status: {response.status_code}")
    print(f"Final URL: {response.request['PATH_INFO']}")
    print(f"Expected: /grants/apply/")
    print(f"✅ Redirects correctly: {'/grants/apply/' in response.request['PATH_INFO']}")
    
    # Clean up user for next test
    User.objects.filter(username='testuser123').delete()
    
    # Test 2: Check that login redirects to grants application  
    print("\n🔑 Test 2: Login Flow")
    # Create user first
    user = User.objects.create_user('logintest', 'login@example.com', 'testpass123!')
    
    login_data = {
        'username': 'logintest',
        'password': 'testpass123!'
    }
    
    response = client.post(reverse('login'), login_data, follow=True)
    print(f"Login status: {response.status_code}")
    print(f"Final URL: {response.request['PATH_INFO']}")
    print(f"Expected: /grants/apply/")
    print(f"✅ Redirects correctly: {'/grants/apply/' in response.request['PATH_INFO']}")
    
    # Test 3: Check landing page CTA for anonymous users
    print("\n🏠 Test 3: Landing Page CTAs")
    client.logout()  # Make sure we're anonymous
    response = client.get('/')
    content = response.content.decode()
    print(f"Landing page status: {response.status_code}")
    print(f"✅ Contains signup button: {'Create account to apply' in content}")
    print(f"✅ Signup URL correct: {reverse('signup') in content}")
    
    # Test 4: Check navbar for authenticated users
    print("\n📱 Test 4: Navbar for Authenticated Users")
    client.login(username='logintest', password='testpass123!')
    response = client.get('/')
    content = response.content.decode()
    print(f"✅ Shows welcome message: {'Welcome' in content}")
    print(f"✅ Shows Apply button: {'Apply' in content}")
    print(f"✅ Shows Check Status: {'Check Status' in content}")
    
    print("\n🎉 All authentication flows tested!")

if __name__ == "__main__":
    test_auth_flow()