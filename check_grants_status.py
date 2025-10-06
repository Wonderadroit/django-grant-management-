#!/usr/bin/env python
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from grants.models import GrantApplication

print("=== GRANT APPLICATION STATUS REPORT ===\n")

# Get all applications
all_apps = GrantApplication.objects.all()
print(f"Total applications: {all_apps.count()}")

# Check status distribution
status_counts = {}
for status_choice in GrantApplication.STATUS_CHOICES:
    status_code = status_choice[0]
    status_label = status_choice[1]
    count = all_apps.filter(status=status_code).count()
    status_counts[status_code] = count
    print(f"  {status_label}: {count}")

print("\n=== DETAILED APPLICATION LIST ===")
for app in all_apps.order_by('-created_at'):
    print(f"ID: {app.id} | Name: {app.full_name}")
    print(f"  Project: {app.project_title}")
    print(f"  Amount Requested: ${app.amount_requested:,}")
    print(f"  Status: {app.get_status_display()}")
    print(f"  Stage: {app.get_current_stage_display()}")
    print(f"  Created: {app.created_at}")
    if app.approved_amount:
        print(f"  Approved Amount: ${app.approved_amount:,}")
    print(f"  ---")

print("\n=== UNDER REVIEW APPLICATIONS ===")
under_review_apps = all_apps.filter(status='under_review')
print(f"Applications with 'under_review' status: {under_review_apps.count()}")

for app in under_review_apps:
    print(f"  ID: {app.id} - {app.full_name} - ${app.amount_requested:,}")

print("\n=== PENDING APPLICATIONS ===")
pending_apps = all_apps.filter(status='pending')
print(f"Applications with 'pending' status: {pending_apps.count()}")

for app in pending_apps:
    print(f"  ID: {app.id} - {app.full_name} - ${app.amount_requested:,}")

print("\n=== APPLICATIONS BY STAGE ===")
for stage_choice in GrantApplication.APPLICATION_STAGES:
    stage_code = stage_choice[0]
    stage_label = stage_choice[1]
    count = all_apps.filter(current_stage=stage_code).count()
    print(f"  {stage_label}: {count}")

# Check if there are any applications that should be under review
print("\n=== RECOMMENDATIONS ===")
if pending_apps.count() > 0:
    print("✅ Found pending applications that can be moved to 'under_review' status")
    print("   Use the admin interface to change their status to 'Under Review'")
else:
    print("ℹ️  No pending applications found")

if under_review_apps.count() == 0:
    print("⚠️  No applications currently marked as 'under_review'")
    print("   You may need to manually set some applications to this status")
else:
    print(f"✅ Found {under_review_apps.count()} applications under review")