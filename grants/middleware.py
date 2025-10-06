"""
Admin Security Middleware for Django Grant Application System
Add this to your middleware in settings.py: 'grants.middleware.AdminSecurityMiddleware'
"""

import logging
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from django.core.cache import cache
import time

logger = logging.getLogger('grants.admin')

class AdminSecurityMiddleware(MiddlewareMixin):
    """
    Security middleware for admin panel
    - Logs all admin actions
    - IP whitelisting for admin access
    - Rate limiting for admin login attempts
    - Session monitoring
    """
    
    def process_request(self, request):
        # Check if this is an admin request
        if request.path.startswith('/admin/') or request.path.startswith(f'/{getattr(settings, "ADMIN_URL", "admin")}/'):
            
            # Log admin access attempts
            self.log_admin_access(request)
            
            # Check IP whitelist if configured
            if hasattr(settings, 'ALLOWED_ADMIN_IPS'):
                if not self.check_ip_whitelist(request):
                    logger.warning(f"Admin access denied for IP: {self.get_client_ip(request)}")
                    return HttpResponseForbidden("Access denied from this IP address")
            
            # Rate limiting for login attempts
            if request.path.endswith('/login/') and request.method == 'POST':
                if not self.check_rate_limit(request):
                    logger.warning(f"Rate limit exceeded for IP: {self.get_client_ip(request)}")
                    return HttpResponseForbidden("Too many login attempts. Please try again later.")
    
    def process_response(self, request, response):
        # Log admin actions
        if (request.path.startswith('/admin/') and 
            request.user.is_authenticated and 
            request.user.is_staff):
            
            self.log_admin_action(request, response)
        
        return response
    
    def get_client_ip(self, request):
        """Get real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def check_ip_whitelist(self, request):
        """Check if IP is in whitelist"""
        client_ip = self.get_client_ip(request)
        allowed_ips = getattr(settings, 'ALLOWED_ADMIN_IPS', [])
        
        # If no whitelist configured, allow all
        if not allowed_ips:
            return True
            
        return client_ip in allowed_ips
    
    def check_rate_limit(self, request):
        """Rate limiting for login attempts"""
        client_ip = self.get_client_ip(request)
        cache_key = f'admin_login_attempts_{client_ip}'
        
        attempts = cache.get(cache_key, 0)
        max_attempts = getattr(settings, 'ADMIN_MAX_LOGIN_ATTEMPTS', 5)
        timeout = getattr(settings, 'ADMIN_LOGIN_TIMEOUT', 300)  # 5 minutes
        
        if attempts >= max_attempts:
            return False
        
        # Increment attempts
        cache.set(cache_key, attempts + 1, timeout)
        return True
    
    def log_admin_access(self, request):
        """Log admin access attempts"""
        if request.user.is_authenticated:
            logger.info(f"Admin access: {request.user.username} from {self.get_client_ip(request)} - {request.path}")
        else:
            logger.info(f"Anonymous admin access from {self.get_client_ip(request)} - {request.path}")
    
    def log_admin_action(self, request, response):
        """Log admin actions"""
        if request.method in ['POST', 'PUT', 'DELETE']:
            action = self.determine_action(request)
            logger.info(f"Admin action: {request.user.username} - {action} - {request.path} - Status: {response.status_code}")
    
    def determine_action(self, request):
        """Determine what action was performed"""
        if 'add' in request.path:
            return 'CREATE'
        elif 'change' in request.path:
            return 'UPDATE'
        elif 'delete' in request.path:
            return 'DELETE'
        elif request.POST.get('action'):
            return f"BULK_ACTION: {request.POST.get('action')}"
        else:
            return 'UNKNOWN'


class AdminSessionMiddleware(MiddlewareMixin):
    """
    Enhanced session security for admin users
    """
    
    def process_request(self, request):
        if (request.user.is_authenticated and 
            request.user.is_staff and 
            request.path.startswith('/admin/')):
            
            # Check session timeout
            self.check_session_timeout(request)
            
            # Update last activity
            request.session['last_activity'] = time.time()
            
            # Check for suspicious activity
            self.check_suspicious_activity(request)
    
    def check_session_timeout(self, request):
        """Check for session timeout"""
        last_activity = request.session.get('last_activity')
        timeout = getattr(settings, 'ADMIN_SESSION_TIMEOUT', 3600)  # 1 hour
        
        if last_activity and (time.time() - last_activity) > timeout:
            logger.warning(f"Admin session timeout for user: {request.user.username}")
            from django.contrib.auth import logout
            logout(request)
    
    def check_suspicious_activity(self, request):
        """Check for suspicious activity patterns"""
        client_ip = self.get_client_ip(request)
        stored_ip = request.session.get('admin_ip')
        
        # Check if IP changed during session
        if stored_ip and stored_ip != client_ip:
            logger.warning(f"IP change detected for admin user {request.user.username}: {stored_ip} -> {client_ip}")
            # Optionally force logout on IP change
            # from django.contrib.auth import logout
            # logout(request)
        
        request.session['admin_ip'] = client_ip
    
    def get_client_ip(self, request):
        """Get real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to automatically create audit logs for admin actions
    """
    
    def process_response(self, request, response):
        if (request.user.is_authenticated and 
            request.user.is_staff and 
            request.path.startswith('/admin/') and
            request.method in ['POST', 'PUT', 'DELETE']):
            
            self.create_audit_log(request, response)
        
        return response
    
    def create_audit_log(self, request, response):
        """Create audit log entry"""
        try:
            from .models import AuditLog
            
            action_type = self.get_action_type(request)
            object_type = self.get_object_type(request)
            object_id = self.get_object_id(request)
            
            AuditLog.objects.create(
                user=request.user,
                action_type=action_type,
                object_type=object_type,
                object_id=object_id,
                description=self.get_description(request, action_type),
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                additional_data=self.get_additional_data(request)
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
    
    def get_action_type(self, request):
        """Determine action type"""
        if 'add' in request.path:
            return 'CREATE'
        elif 'change' in request.path:
            return 'UPDATE'
        elif 'delete' in request.path:
            return 'DELETE'
        elif request.POST.get('action'):
            return 'BULK_ACTION'
        return 'OTHER'
    
    def get_object_type(self, request):
        """Extract object type from URL"""
        path_parts = request.path.split('/')
        if len(path_parts) >= 4:
            return path_parts[3]  # e.g., /admin/grants/grantapplication/
        return 'unknown'
    
    def get_object_id(self, request):
        """Extract object ID from URL"""
        path_parts = request.path.split('/')
        if len(path_parts) >= 5 and path_parts[4].isdigit():
            return path_parts[4]
        return None
    
    def get_description(self, request, action_type):
        """Generate description of the action"""
        if action_type == 'BULK_ACTION':
            action = request.POST.get('action', 'unknown')
            count = len(request.POST.getlist('_selected_action'))
            return f"Bulk action '{action}' on {count} items"
        else:
            return f"{action_type} operation on {self.get_object_type(request)}"
    
    def get_additional_data(self, request):
        """Get additional data for audit log"""
        data = {}
        
        if request.POST.get('action'):
            data['bulk_action'] = request.POST.get('action')
            data['selected_items'] = request.POST.getlist('_selected_action')
        
        return data
    
    def get_client_ip(self, request):
        """Get real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip