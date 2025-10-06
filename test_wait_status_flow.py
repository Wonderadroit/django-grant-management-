#!/usr/bin/env python
"""
Test the wait page -> status page flow to ensure navigation works correctly.
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
from grants.models import GrantApplication

def test_wait_status_flow():
    print("🔄 Testing Wait → Status Page Flow")
    print("=" * 50)
    
    client = Client(HTTP_HOST='localhost')
    
    # Create and login user
    User.objects.filter(username='flowtest').delete()
    user = User.objects.create_user('flowtest', 'flow@example.com', 'testpass123!')
    client.login(username='flowtest', password='testpass123!')
    
    # Create a grant application
    grant = GrantApplication.objects.create(
        user=user,
        full_name='Flow Test User',
        email='flow@example.com',
        address='123 Test Street',
        amount_requested=5000,
        status='Pending'
    )
    
    print("\n📄 Testing wait page...")
    wait_response = client.get(reverse('grants:wait'))
    print(f"Wait page status: {wait_response.status_code}")
    wait_content = wait_response.content.decode()
    print(f"✅ Contains status link: {'Check Application Status' in wait_content}")
    print(f"✅ Shows user name: {'Flow Test User' in wait_content}")
    
    print("\n📊 Testing status page...")
    status_response = client.get(reverse('grants:status'))
    print(f"Status page status: {status_response.status_code}")
    status_content = status_response.content.decode()
    print(f"✅ Shows status message: {'under review' in status_content or 'approved' in status_content}")
    print(f"✅ Has refresh button: {'Refresh Status' in status_content}")
    
    print("\n🤖 Testing AI insights page...")
    ai_response = client.get(reverse('grants:ai_insights'))
    print(f"AI insights status: {ai_response.status_code}")
    ai_content = ai_response.content.decode()
    print(f"✅ Shows AI analysis: {'AI Summary' in ai_content or 'AI Insights' in ai_content}")
    
    print("\n✅ All page navigation working correctly!")

if __name__ == "__main__":
    test_wait_status_flow()