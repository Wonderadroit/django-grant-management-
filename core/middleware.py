# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.http import Http404
from django.conf import settings

class AdminSecurityMiddleware:
    """
    Middleware to secure admin access and provide better error handling
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is an admin request
        if request.path.startswith('/djf-admin-portal/'):
            # Hide admin in production if user is not staff
            if not settings.DEBUG and not (request.user.is_authenticated and request.user.is_staff):
                # Return 404 instead of login redirect for security
                raise Http404("Page not found")
                
            # In development, redirect to login if not authenticated
            if settings.DEBUG and not request.user.is_authenticated:
                messages.warning(request, "Admin access requires staff authentication")
                return redirect(f"{reverse('login')}?next={request.path}")
                
            # Check if user has admin access
            if request.user.is_authenticated and not request.user.is_staff:
                messages.error(request, "You don't have permission to access the admin panel")
                return redirect('home')

        response = self.get_response(request)
        return response

class HideAdminMiddleware:
    """
    Middleware to completely hide admin URLs from regular users
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle old admin URL - always return 404
        if request.path.startswith('/admin/'):
            raise Http404("Page not found")
            
        # Handle direct admin access attempts
        if request.path.startswith('/djf-admin-portal/'):
            # Allow access only to authenticated staff users
            if not (request.user.is_authenticated and request.user.is_staff):
                # Return 404 to hide the existence of admin panel
                raise Http404("Page not found")

        response = self.get_response(request)
        return response