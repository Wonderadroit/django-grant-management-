#!/usr/bin/env python
"""
Test signup form validation to identify common issues.
"""
import os
import sys
import django

# Setup Django environment  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.forms import SignUpForm

def test_signup_form():
    print("🔍 Testing Signup Form Validation")
    print("=" * 50)
    
    # Test 1: Valid data
    print("\n✅ Test 1: Valid signup data")
    valid_data = {
        'username': 'testuser123',
        'email': 'test@example.com', 
        'password1': 'ComplexPass123!',
        'password2': 'ComplexPass123!'
    }
    form = SignUpForm(valid_data)
    print(f"Form valid: {form.is_valid()}")
    if not form.is_valid():
        print(f"Errors: {form.errors}")
    
    # Test 2: Password mismatch
    print("\n❌ Test 2: Password mismatch")
    mismatch_data = {
        'username': 'testuser456',
        'email': 'test2@example.com',
        'password1': 'ComplexPass123!',
        'password2': 'DifferentPass456!'
    }
    form = SignUpForm(mismatch_data)
    print(f"Form valid: {form.is_valid()}")
    if not form.is_valid():
        print(f"Expected password error: {form.errors}")
    
    # Test 3: Weak password
    print("\n❌ Test 3: Weak password")
    weak_data = {
        'username': 'testuser789',
        'email': 'test3@example.com',
        'password1': '123',
        'password2': '123'
    }
    form = SignUpForm(weak_data)
    print(f"Form valid: {form.is_valid()}")
    if not form.is_valid():
        print(f"Expected validation errors: {form.errors}")
    
    # Test 4: Missing email
    print("\n❌ Test 4: Missing email")
    no_email_data = {
        'username': 'testuser999',
        'password1': 'ComplexPass123!',
        'password2': 'ComplexPass123!'
    }
    form = SignUpForm(no_email_data)
    print(f"Form valid: {form.is_valid()}")
    if not form.is_valid():
        print(f"Expected email error: {form.errors}")

if __name__ == "__main__":
    test_signup_form()