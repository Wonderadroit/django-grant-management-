#!/usr/bin/env python
"""
Demo script showing how the AI-powered grant analysis works.
Run this to see the AI feature in action.
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from grants.ai import analyze_text

def demo_ai_analysis():
    print("🤖 AI-Powered Grant Analysis Demo")
    print("=" * 50)
    
    # Sample grant applications
    sample_grants = [
        {
            "name": "Sarah Johnson",
            "address": "456 Oak Street, Springfield",
            "amount": "$5,000",
            "description": "Educational technology startup focused on providing affordable coding bootcamps for underserved communities"
        },
        {
            "name": "Mike Chen", 
            "address": "789 Pine Avenue, Metro City",
            "amount": "$10,000", 
            "description": "Community garden project to provide fresh organic vegetables and nutrition education to low-income families"
        },
        {
            "name": "Elena Rodriguez",
            "address": "321 Elm Drive, Riverside",
            "amount": "$1,000",
            "description": "Small craft business making handmade jewelry to support single mothers in my neighborhood"
        }
    ]
    
    for i, grant in enumerate(sample_grants, 1):
        print(f"\n📋 Grant Application #{i}")
        print(f"Name: {grant['name']}")
        print(f"Amount: {grant['amount']}")
        print(f"Address: {grant['address']}")
        print(f"Description: {grant['description']}")
        
        # Create the text that would be analyzed
        text = f"Full name: {grant['name']}. Address: {grant['address']}. Amount: {grant['amount']}. {grant['description']}"
        
        # Run AI analysis
        result = analyze_text(text)
        
        print(f"\n🔍 AI Analysis:")
        print(f"Summary: {result['summary']}")
        print(f"Impact Score: {result['score'] if result['score'] else 'N/A'}")
        print(f"Model: {result['note']}")
        print("-" * 50)

if __name__ == "__main__":
    demo_ai_analysis()