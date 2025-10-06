# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.contrib.admin.apps import AdminConfig
from django.utils.translation import gettext_lazy as _

class CustomAdminConfig(AdminConfig):
    """Custom admin configuration for branding"""
    default_site = 'core.admin.CustomAdminSite'

class CustomAdminSite(admin.AdminSite):
    """Custom admin site with David Johnson Foundation branding"""
    
    # Branding
    site_header = _("David Johnson Foundation - Grant Management")
    site_title = _("DJF Grant Admin")
    index_title = _("Grant Application Management Portal")
    site_url = "/"
    
    # Security
    enable_nav_sidebar = True
    
    def has_permission(self, request):
        """
        Only allow access to staff users
        """
        return request.user.is_active and request.user.is_staff
    
    def index(self, request, extra_context=None):
        """
        Add custom context to admin index
        """
        extra_context = extra_context or {}
        extra_context.update({
            'custom_message': 'Welcome to the David Johnson Foundation Grant Management System',
            'site_description': 'Manage grant applications, track progress, and support our community initiatives.',
        })
        return super().index(request, extra_context)

# Create custom admin site instance
admin_site = CustomAdminSite(name='djf_admin')

# Additional admin styling and configuration
def admin_view_middleware(get_response):
    """Middleware to add custom styling to admin views"""
    def middleware(request):
        response = get_response(request)
        if request.path.startswith('/djf-admin-portal/'):
            # Add custom CSS for admin branding
            if hasattr(response, 'content') and b'</head>' in response.content:
                custom_css = """
                <style>
                    #header { background: #1f4e79; }
                    #branding h1 { color: #fff; }
                    #branding h1 a:link, #branding h1 a:visited { color: #fff; }
                    .module caption { background: #1f4e79; color: #fff; }
                    .module h2 { background: #1f4e79; color: #fff; }
                    #user-tools a { color: #fff; }
                    #user-tools a:hover { color: #ccc; }
                </style>
                """
                response.content = response.content.replace(
                    b'</head>', 
                    custom_css.encode() + b'</head>'
                )
        return response
    return middleware