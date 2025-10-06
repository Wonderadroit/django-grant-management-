# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.urls import path, include  # add this
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import Http404
from .views import landing, admin_access, custom_404_view, health_check

# Custom admin site configuration
admin.site.site_header = "Dave Johnson Foundation - Grant Management"
admin.site.site_title = "DJF Grant Admin"
admin.site.index_title = "Grant Application Management Portal"
admin.site.site_url = "/"  # Link to main site from admin

def admin_404_view(request):
    """Return 404 for old admin URL"""
    raise Http404("Page not found")

urlpatterns = [
    path('', landing, name='home'),
    path('health/', health_check, name='health_check'),  # Health check for Render
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    path('admin/', admin_404_view),  # Hide old admin URL
    path('secure-admin-access/', admin_access, name='admin_access'),  # Secure admin access for superusers
    path('djf-admin-portal/', admin.site.urls),  # Use default admin site
    path('accounts/', include('accounts.urls')),  # Use accounts for authentication
    path("", include("app.urls")),  # app urls
    path('grants/', include('grants.urls')),
]

# Custom 404 handler
handler404 = custom_404_view

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
