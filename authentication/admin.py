# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db.models import Count, Q
from grants.models import GrantApplication

# Unregister the default User admin
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'full_name_display', 'application_status', 'date_joined', 'last_login', 'is_active')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    actions = ['activate_users', 'deactivate_users', 'send_welcome_email', 'export_users_csv']
    list_per_page = 25
    date_hierarchy = 'date_joined'
    
    def full_name_display(self, obj):
        """Display user's full name or username"""
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        if full_name:
            return format_html('<strong>{}</strong>', full_name)
        return obj.username
    full_name_display.short_description = 'Full Name'
    
    def application_status(self, obj):
        """Show grant application status for this user"""
        try:
            grant = GrantApplication.objects.get(user=obj)
            colors = {
                'pending': '#ffc107',
                'under_review': '#007bff', 
                'approved': '#28a745',
                'rejected': '#dc3545',
                'on_hold': '#6c757d'
            }
            color = colors.get(grant.status, '#6c757d')
            return format_html(
                '<a href="/admin/grants/grantapplication/{}/change/" style="color: {}; text-decoration: none;"><span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span></a>',
                grant.id,
                color,
                color,
                grant.get_status_display()
            )
        except GrantApplication.DoesNotExist:
            return format_html('<span style="color: #6c757d; font-style: italic;">No Application</span>')
    application_status.short_description = 'Grant Status'
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} users")
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        # Don't deactivate staff users
        non_staff = queryset.filter(is_staff=False)
        updated = non_staff.update(is_active=False)
        if updated < queryset.count():
            self.message_user(request, f"Deactivated {updated} users (staff users were skipped)")
        else:
            self.message_user(request, f"Deactivated {updated} users")
    deactivate_users.short_description = 'Deactivate selected users'
    
    def send_welcome_email(self, request, queryset):
        """Send welcome email to selected users"""
        from django.core.mail import send_mail
        sent = 0
        for user in queryset:
            if user.email:
                send_mail(
                    'Welcome to David Johnson Foundation',
                    f'''Dear {user.first_name or user.username},

Welcome to the David Johnson Foundation grant platform!

Your account has been successfully created and you can now:
- Apply for grants ranging from $10,000 to $30,000
- Track your application status
- Receive updates on your grant progress
- Access our support resources

To get started:
1. Log in to your account at our website
2. Complete your grant application
3. Submit required documentation
4. Track your progress through our review process

If you have any questions or need assistance, please don't hesitate to contact our support team.

Thank you for joining our community of changemakers!

Best regards,
David Johnson Foundation Team''',
                    None,
                    [user.email],
                    fail_silently=True,
                )
                sent += 1
        
        self.message_user(request, f"Sent welcome emails to {sent} users")
    send_welcome_email.short_description = 'Send welcome email'
    
    def export_users_csv(self, request, queryset):
        """Export users to CSV"""
        from django.http import HttpResponse
        from datetime import datetime
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Email', 'First Name', 'Last Name', 'Is Active', 
            'Is Staff', 'Date Joined', 'Last Login', 'Has Application', 
            'Application Status'
        ])
        
        for user in queryset:
            try:
                grant = GrantApplication.objects.get(user=user)
                has_application = 'Yes'
                application_status = grant.get_status_display()
            except GrantApplication.DoesNotExist:
                has_application = 'No'
                application_status = 'N/A'
            
            writer.writerow([
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.is_active,
                user.is_staff,
                user.date_joined.strftime('%Y-%m-%d %H:%M'),
                user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
                has_application,
                application_status
            ])
        
        return response
    export_users_csv.short_description = 'Export users to CSV'
    
    # Add custom fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('Grant Information', {
            'fields': (),
            'description': 'Grant application information is managed in the Grants section.'
        }),
    )
