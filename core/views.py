from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import Http404, JsonResponse
from grants.forms import GrantApplicationForm
import os

def health_check(request):
    """Health check endpoint for Render"""
    return JsonResponse({
        'status': 'healthy',
        'version': '1.0.0',
        'database': 'connected',
        'environment': 'production' if not os.environ.get('DEBUG', 'false').lower() == 'true' else 'development'
    })

def landing(request):
    # Provide an empty form for the landing page; form posts to /grants/apply/
    form = GrantApplicationForm()
    return render(request, 'landing.html', {'form': form})

def is_staff(user):
    """Check if user is staff"""
    return user.is_staff

def is_superuser(user):
    """Check if user is superuser"""
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def admin_access(request):
    """Secure access point for admin - only for superusers"""
    return redirect('/djf-admin-portal/')

def admin_access_denied(request):
    """Show access denied message for non-staff users trying to access admin"""
    messages.error(request, "Access denied. This area is restricted to authorized personnel only.")
    return redirect('home')

def custom_404_view(request, exception=None):
    """Custom 404 handler"""
    return render(request, '404.html', status=404)
