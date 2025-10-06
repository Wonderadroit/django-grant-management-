#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from grants.models import GrantApplication

print("=== APPROVED GRANT APPLICATIONS ===")
print("ID | Requested Amount | Approved Amount | Name")
print("-" * 60)

for app in GrantApplication.objects.filter(status='approved').order_by('id'):
    approved_amt = app.approved_amount if app.approved_amount else 0
    print(f"{app.id:2d} | ${app.amount_requested:>12,} | ${approved_amt:>13,} | {app.full_name}")

print("\n=== POTENTIAL ISSUES ===")
issues = GrantApplication.objects.filter(
    status='approved', 
    amount_requested__gt=10000,
    approved_amount=10000
)

if issues.exists():
    print("Found applications that requested >$10k but were approved for exactly $10k:")
    for app in issues:
        print(f"ID {app.id}: Requested ${app.amount_requested:,}, Approved ${app.approved_amount:,}")
else:
    print("No issues found with $10k capping.")