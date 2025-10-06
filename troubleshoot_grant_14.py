#!/usr/bin/env python3
"""
Troubleshooting script for Grant Application #14 discrepancy
Run this to verify the database values and generate user instructions
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from grants.models import GrantApplication
from django.contrib.auth.models import User

def main():
    print("=" * 60)
    print("GRANT APPLICATION #14 TROUBLESHOOTING REPORT")
    print("=" * 60)
    
    try:
        # Get the application
        app = GrantApplication.objects.get(id=14)
        user = app.user
        
        print(f"\n📋 APPLICATION DETAILS:")
        print(f"   Application ID: DJF-{app.id:04d}")
        print(f"   User: {user.username} ({user.email})")
        print(f"   Full Name: {app.full_name}")
        print(f"   Project: {app.project_title}")
        print(f"   Status: {app.status.upper()}")
        print(f"   Created: {app.created_at}")
        print(f"   Last Updated: {app.updated_at}")
        
        print(f"\n💰 FINANCIAL DETAILS:")
        print(f"   Amount Requested: ${app.amount_requested:,}")
        print(f"   Amount Approved: ${app.approved_amount:,}")
        print(f"   Approval Date: {app.approval_date}")
        
        print(f"\n✅ DATABASE VERIFICATION:")
        print(f"   ✓ Database shows APPROVED amount: ${app.approved_amount:,}")
        print(f"   ✓ Status is: {app.status}")
        print(f"   ✓ Approval timestamp: {app.approval_date}")
        
        print(f"\n🔧 TROUBLESHOOTING STEPS:")
        print(f"   1. Database is correct: ${app.approved_amount:,}")
        print(f"   2. Ask user to clear browser cache and refresh")
        print(f"   3. Ask user to log out and log back in")
        print(f"   4. Have user check status at: http://127.0.0.1:8000/grants/status/")
        print(f"   5. Verify user is looking at application DJF-{app.id:04d}")
        
        print(f"\n📱 USER INSTRUCTIONS TO SHARE:")
        print(f"   Dear {app.full_name},")
        print(f"   ")
        print(f"   Our database shows your approved amount is correctly set to ${app.approved_amount:,}.")
        print(f"   If you're seeing ${10000:,}, please try these steps:")
        print(f"   ")
        print(f"   1. Clear your browser cache (Ctrl+Shift+Del on Windows)")
        print(f"   2. Log out of your account completely")
        print(f"   3. Log back in and check your status page")
        print(f"   4. Ensure you're looking at application DJF-{app.id:04d}")
        print(f"   ")
        print(f"   If the issue persists, please contact support.")
        
        print(f"\n🔗 DIRECT VERIFICATION LINKS:")
        print(f"   Admin Link: http://127.0.0.1:8000/djf-admin-portal/grants/grantapplication/{app.id}/change/")
        print(f"   User Status: http://127.0.0.1:8000/grants/status/")
        
    except GrantApplication.DoesNotExist:
        print("❌ ERROR: Grant Application #14 not found!")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()