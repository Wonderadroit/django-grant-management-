from django.contrib import admin
from django import forms
from .models import (
    GrantApplication, DocumentType, GrantDocument, Message, SuccessStory, SuccessStoryImage,
    ProgressReport, FundDisbursement, ExpenseReport, GrantAnalytics, AuditLog, GrantSettings
)
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg
from django.http import HttpResponse
from django.contrib.admin import SimpleListFilter
import json
import csv
from datetime import datetime, timedelta

# Custom Form for Grant Application Admin
class GrantApplicationAdminForm(forms.ModelForm):
    class Meta:
        model = GrantApplication
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'approved_amount' in self.fields:
            self.fields['approved_amount'].widget = forms.NumberInput(attrs={
                'style': 'font-size: 16px; font-weight: bold; color: #28a745; border: 2px solid #28a745; padding: 8px;',
                'placeholder': 'Enter any amount you want to approve'
            })
            if self.instance and self.instance.amount_requested:
                self.fields['approved_amount'].help_text = (
                    f"💡 <strong>Tip:</strong> Applicant requested <strong>${self.instance.amount_requested:,}</strong>. "
                    f"You can approve <strong>any amount</strong> - more, less, or exactly what they requested. "
                    f"<br>💰 <strong>Examples:</strong> ${self.instance.amount_requested//2:,} (half), "
                    f"${self.instance.amount_requested:,} (full), ${int(self.instance.amount_requested * 1.2):,} (20% more)"
                )

# Custom Filters
class StatusFilter(SimpleListFilter):
    title = 'Application Status'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return (
            ('pending', 'Pending Review'),
            ('under_review', 'Under Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('needs_action', 'Needs Action'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'needs_action':
            return queryset.filter(status='pending', created_at__lte=timezone.now() - timedelta(hours=24))
        elif self.value():
            return queryset.filter(status=self.value())
        return queryset

class AmountRangeFilter(SimpleListFilter):
    title = 'Grant Amount Range'
    parameter_name = 'amount_range'
    
    def lookups(self, request, model_admin):
        return (
            ('small', '$10,000 - $15,000'),
            ('medium', '$15,001 - $25,000'),
            ('large', '$25,001 - $30,000'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'small':
            return queryset.filter(amount_requested__gte=10000, amount_requested__lte=15000)
        elif self.value() == 'medium':
            return queryset.filter(amount_requested__gte=15001, amount_requested__lte=25000)
        elif self.value() == 'large':
            return queryset.filter(amount_requested__gte=25001, amount_requested__lte=30000)
        return queryset

@admin.register(GrantApplication)
class GrantApplicationAdmin(admin.ModelAdmin):
    form = GrantApplicationAdminForm
    list_display = ('id', 'display_name', 'requested_amount_display', 'amount_comparison', 'status_badge', 'stage_badge', 'review_application', 'approval_date', 'created_at', 'days_pending')
    
    class Media:
        css = {
            'all': ('admin/css/grant_admin_enhancements.css',)
        }
        js = ('admin/js/grant_admin_enhancements.js',)
    list_filter = (StatusFilter, AmountRangeFilter, 'current_stage', 'project_category', 'organization_type', 'created_at', 'approval_date', 'documents_complete', 'documents_verified')
    search_fields = ('full_name', 'email', 'user__username', 'project_title', 'organization_name')
    actions = ['mark_approved', 'approve_with_custom_amount', 'mark_rejected', 'mark_under_review', 'advance_stage', 'schedule_interview', 'export_to_csv', 'export_detailed_report', 'send_followup_email']
    readonly_fields = ('user', 'created_at', 'updated_at', 'last_activity', 'progress_percentage')
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_display_links = ('id', 'display_name')  # Make these clickable to view details
    
    fieldsets = (
        ('📋 Application Review', {
            'fields': ('user', 'current_stage', 'status', 'progress_percentage'),
            'classes': ('wide',)
        }),
        ('💰 Financial Decision - CLICK HERE TO REVIEW AMOUNTS', {
            'fields': ('amount_requested', 'approved_amount', 'approval_date', 'approval_notes'),
            'classes': ('wide', 'highlight-section'),
            'description': '⚠️ IMPORTANT: You can approve ANY amount regardless of what the applicant requested. '
                         'The "Amount Requested" field shows what they asked for. Set the "Approved Amount" to whatever you determine is appropriate. '
                         'You have complete control over the final approved amount!'
        }),
        ('👤 Personal Details', {
            'fields': ('full_name', 'email', 'phone', 'address'),
            'classes': ('collapse',)
        }),
        ('🏢 Organization Details (Optional)', {
            'fields': ('organization_name', 'organization_type', 'tax_id', 'years_established', 'website'),
            'description': 'These fields are optional for individual applicants',
            'classes': ('collapse',)
        }),
        ('📊 Project Information - REVIEW THIS SECTION', {
            'fields': ('project_title', 'project_category', 'project_description', 'project_goals', 'target_beneficiaries', 'expected_impact'),
            'classes': ('wide',)
        }),
        ('💵 Budget Details', {
            'fields': ('budget_breakdown', 'other_funding'),
            'classes': ('wide',)
        }),
        ('📅 Timeline & Implementation', {
            'fields': ('project_start_date', 'project_duration', 'implementation_plan'),
            'classes': ('collapse',)
        }),
        ('🎯 Experience & Additional Info', {
            'fields': ('experience', 'team_members', 'challenges', 'sustainability', 'additional_info'),
            'classes': ('collapse',)
        }),
        ('📄 Document Verification', {
            'fields': ('documents_complete', 'documents_verified', 'verification_date'),
            'classes': ('collapse',)
        }),
        ('🎤 Interview Information', {
            'fields': ('interview_scheduled', 'interview_date', 'interview_notes', 'interview_completed'),
            'classes': ('collapse',)
        }),
        ('ℹ️ System Info', {
            'fields': ('created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )

    def display_name(self, obj):
        """Display applicant name with type indicator and project title"""
        project_info = f"Project: {obj.project_title[:50]}..." if len(obj.project_title) > 50 else f"Project: {obj.project_title}"
        
        if obj.organization_name:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">Organization: {}</small><br><small style="color: #17a2b8;">{}</small>',
                obj.full_name,
                obj.organization_name,
                project_info
            )
        else:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">Individual Applicant</small><br><small style="color: #17a2b8;">{}</small>',
                obj.full_name,
                project_info
            )
    display_name.short_description = 'Applicant & Project'

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'under_review': '#007bff', 
            'approved': '#28a745',
            'rejected': '#dc3545',
            'on_hold': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def stage_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'eligibility': '#17a2b8',
            'details': '#007bff',
            'documents': '#ffc107',
            'review': '#fd7e14',
            'interview': '#e83e8c',
            'decision': '#20c997',
            'completed': '#28a745'
        }
        color = colors.get(obj.current_stage, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_current_stage_display()
        )
    stage_badge.short_description = 'Stage'

    def amount_comparison(self, obj):
        """Show requested vs approved amounts with visual indicators"""
        requested = obj.amount_requested
        approved = obj.approved_amount
        
        if obj.status == 'approved' and approved:
            if approved == requested:
                # Full amount approved
                return format_html(
                    '<div style="text-align: center;">'
                    '<div style="color: #28a745; font-weight: bold;">${}</div>'
                    '<div style="color: #6c757d; font-size: 11px;">✓ Full Amount</div>'
                    '</div>',
                    f"{approved:,}"
                )
            elif approved > requested:
                # More than requested
                return format_html(
                    '<div style="text-align: center;">'
                    '<div style="color: #17a2b8; font-weight: bold;">${}</div>'
                    '<div style="color: #6c757d; font-size: 11px;">↑ +${} extra</div>'
                    '</div>',
                    f"{approved:,}", f"{approved - requested:,}"
                )
            else:
                # Less than requested
                return format_html(
                    '<div style="text-align: center;">'
                    '<div style="color: #fd7e14; font-weight: bold;">${}</div>'
                    '<div style="color: #6c757d; font-size: 11px;">↓ ${} less</div>'
                    '</div>',
                    f"{approved:,}", f"{requested - approved:,}"
                )
        else:
            # Not approved yet
            return format_html(
                '<div style="text-align: center;">'
                '<div style="color: #6c757d; font-weight: bold;">${}</div>'
                '<div style="color: #6c757d; font-size: 11px;">Requested</div>'
                '</div>',
                f"{requested:,}"
            )
    amount_comparison.short_description = 'Amount Analysis'
    
    def requested_amount_display(self, obj):
        """Display requested amount prominently"""
        formatted_amount = f"{obj.amount_requested:,}"
        return format_html(
            '<div style="text-align: center; font-weight: bold; color: #007bff; font-size: 14px;">'  
            '${}</div>'
            '<div style="text-align: center; font-size: 11px; color: #6c757d;">Requested</div>',
            formatted_amount
        )
    requested_amount_display.short_description = 'Amount Requested'

    def mark_approved(self, request, queryset):
        updated = 0
        for grant in queryset:
            grant._updated_by = request.user  # Track who made the change
            grant.status = 'approved'
            grant.approval_date = timezone.now()
            if not grant.approved_amount:
                grant.approved_amount = grant.amount_requested
            grant.save()
            updated += 1
            
        self.message_user(request, f"Marked {updated} applications as approved. Notification emails will be sent automatically.")
    mark_approved.short_description = 'Approve selected applications (full requested amount)'

    def approve_with_custom_amount(self, request, queryset):
        """Custom action that redirects to a page where admin can set individual approval amounts"""
        if queryset.count() > 5:
            self.message_user(request, "Please select 5 or fewer applications for custom amount approval.", level='WARNING')
            return
            
        # For now, show a helpful message about using the edit page
        self.message_user(
            request, 
            f"To set custom approval amounts: Click on each application individually, "
            f"edit the 'Approved Amount' field to your desired amount (can be different from requested), "
            f"change status to 'Approved', and save. You have full control over the approved amount!",
            level='INFO'
        )
    approve_with_custom_amount.short_description = '💰 Approve with custom amounts (click each individually)'

    def mark_rejected(self, request, queryset):
        updated = 0
        for grant in queryset:
            grant._updated_by = request.user  # Track who made the change
            grant.status = 'rejected'
            grant.save()
            updated += 1
            
        self.message_user(request, f"Marked {updated} applications as rejected. Notification emails will be sent automatically.")
    mark_rejected.short_description = 'Reject selected applications'

    def mark_under_review(self, request, queryset):
        updated = 0
        for grant in queryset:
            grant._updated_by = request.user  # Track who made the change
            grant.status = 'under_review'
            grant.current_stage = 'review'
            grant.save()
            updated += 1
            
        self.message_user(request, f"Marked {updated} applications as under review. These applications are now visible in the 'Under Review' filter. Use the blue 'Review Details' buttons to examine each application.")
    mark_under_review.short_description = '🔍 Mark as under review (makes them visible for detailed review)'
    
    def advance_stage(self, request, queryset):
        """Advance applications to next stage"""
        stage_progression = {
            'draft': 'eligibility',
            'eligibility': 'details',
            'details': 'documents',
            'documents': 'review',
            'review': 'interview',
            'interview': 'decision',
            'decision': 'completed'
        }
        
        updated = 0
        for grant in queryset:
            next_stage = stage_progression.get(grant.current_stage)
            if next_stage:
                grant.current_stage = next_stage
                grant.progress_percentage = grant.get_progress_percentage()
                grant.save()
                updated += 1
        
        self.message_user(request, f"Advanced {updated} applications to next stage")
    advance_stage.short_description = 'Advance to next stage'
    
    def days_pending(self, obj):
        """Show how many days the application has been pending"""
        if obj.status == 'pending':
            days = (timezone.now() - obj.created_at).days
            color = '#dc3545' if days > 3 else '#ffc107' if days > 1 else '#28a745'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} days</span>',
                color,
                days
            )
        return '-'
    days_pending.short_description = 'Days Pending'
    
    def review_application(self, obj):
        """Add a direct link to review the application in detail"""
        if obj.status in ['pending', 'under_review']:
            url = reverse('admin:grants_grantapplication_change', args=[obj.pk])
            return format_html(
                '<a href="{}" style="background-color: #007bff; color: white; padding: 6px 12px; '
                'text-decoration: none; border-radius: 4px; font-weight: bold;">'
                '📋 Review Details</a>',
                url
            )
        elif obj.status == 'approved':
            url = reverse('admin:grants_grantapplication_change', args=[obj.pk])
            return format_html(
                '<a href="{}" style="background-color: #28a745; color: white; padding: 6px 12px; '
                'text-decoration: none; border-radius: 4px; font-weight: bold;">'
                '✅ View Approved</a>',
                url
            )
        else:
            url = reverse('admin:grants_grantapplication_change', args=[obj.pk])
            return format_html(
                '<a href="{}" style="background-color: #6c757d; color: white; padding: 6px 12px; '
                'text-decoration: none; border-radius: 4px; font-weight: bold;">'
                '👁️ View Details</a>',
                url
            )
    review_application.short_description = 'Actions'

    def export_to_csv(self, request, queryset):
        """Export selected applications to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="grant_applications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Full Name', 'Email', 'Organization', 'Project Title', 
            'Amount Requested', 'Approved Amount', 'Status', 'Stage',
            'Project Category', 'Created Date', 'Approval Date'
        ])
        
        for obj in queryset:
            writer.writerow([
                f'DJF-{obj.id:04d}',
                obj.full_name,
                obj.email,
                obj.organization_name or 'Individual',
                obj.project_title,
                obj.amount_requested,
                obj.approved_amount or '',
                obj.get_status_display(),
                obj.get_current_stage_display(),
                obj.get_project_category_display(),
                obj.created_at.strftime('%Y-%m-%d'),
                obj.approval_date.strftime('%Y-%m-%d') if obj.approval_date else ''
            ])
        
        return response
    export_to_csv.short_description = 'Export selected to CSV'

    def export_detailed_report(self, request, queryset):
        """Export detailed application report with all information"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="detailed_grant_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Application ID', 'Full Name', 'Email', 'Phone', 'Address',
            'Organization Name', 'Organization Type', 'Tax ID', 'Website',
            'Project Title', 'Project Category', 'Project Description',
            'Amount Requested', 'Approved Amount', 'Budget Breakdown',
            'Project Goals', 'Target Beneficiaries', 'Expected Impact',
            'Experience', 'Implementation Plan', 'Sustainability',
            'Status', 'Current Stage', 'Created Date', 'Approval Date',
            'Processing Days', 'Documents Complete', 'Interview Scheduled'
        ])
        
        for obj in queryset:
            processing_days = ''
            if obj.approval_date:
                processing_days = (obj.approval_date.date() - obj.created_at.date()).days
            
            writer.writerow([
                f'DJF-{obj.id:04d}',
                obj.full_name,
                obj.email,
                obj.phone,
                obj.address,
                obj.organization_name or '',
                obj.get_organization_type_display() if obj.organization_type else '',
                obj.tax_id or '',
                obj.website or '',
                obj.project_title,
                obj.get_project_category_display(),
                obj.project_description,
                obj.amount_requested,
                obj.approved_amount or '',
                obj.budget_breakdown,
                obj.project_goals,
                obj.target_beneficiaries,
                obj.expected_impact,
                obj.experience,
                obj.implementation_plan,
                obj.sustainability,
                obj.get_status_display(),
                obj.get_current_stage_display(),
                obj.created_at.strftime('%Y-%m-%d %H:%M'),
                obj.approval_date.strftime('%Y-%m-%d %H:%M') if obj.approval_date else '',
                processing_days,
                obj.documents_complete,
                obj.interview_scheduled
            ])
        
        return response
    export_detailed_report.short_description = 'Export detailed report'

    def changelist_view(self, request, extra_context=None):
        """Add custom context for better navigation"""
        extra_context = extra_context or {}
        
        # Count applications by status for quick navigation
        from django.db.models import Count
        
        status_counts = {}
        for status_code, status_label in GrantApplication.STATUS_CHOICES:
            count = GrantApplication.objects.filter(status=status_code).count()
            status_counts[status_code] = {'label': status_label, 'count': count}
        
        extra_context['status_counts'] = status_counts
        extra_context['quick_links'] = [
            {'url': '?status=under_review', 'label': f'🔍 Under Review ({status_counts.get("under_review", {}).get("count", 0)})', 'class': 'btn-info'},
            {'url': '?status=pending', 'label': f'⏳ Pending ({status_counts.get("pending", {}).get("count", 0)})', 'class': 'btn-warning'},
            {'url': '?status=approved', 'label': f'✅ Approved ({status_counts.get("approved", {}).get("count", 0)})', 'class': 'btn-success'},
            {'url': '?status=rejected', 'label': f'❌ Rejected ({status_counts.get("rejected", {}).get("count", 0)})', 'class': 'btn-danger'},
        ]
        
        return super().changelist_view(request, extra_context=extra_context)

    def send_followup_email(self, request, queryset):
        """Send follow-up email to applicants"""
        sent = 0
        for grant in queryset:
            if grant.email and grant.status == 'pending':
                send_mail(
                    'Grant Application Status Update - Dave Johnson Foundation',
                    f'''Dear {grant.full_name},

We wanted to provide you with an update on your grant application for "{grant.project_title}".

Application Details:
- Application ID: DJF-{grant.id:04d}
- Current Status: Under Review
- Submitted: {grant.created_at.strftime('%B %d, %Y')}

Your application is currently in our review process. We appreciate your patience as our committee carefully evaluates each submission.

You can check your application status anytime by logging into your account at our website and visiting the "Check Status" page.

If you have any questions or need to provide additional information, please don't hesitate to contact us.

Thank you for your continued interest in the Dave Johnson Foundation.

Best regards,
Dave Johnson Foundation Review Team''',
                    None,
                    [grant.email],
                    fail_silently=True,
                )
                sent += 1
        
        self.message_user(request, f"Sent follow-up emails to {sent} applicants")
    send_followup_email.short_description = 'Send follow-up email'


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'required', 'max_file_size_mb', 'allowed_extensions', 'display_order')
    list_filter = ('required',)
    search_fields = ('name', 'description')
    ordering = ('display_order', 'name')
    
    def max_file_size_mb(self, obj):
        return f"{obj.max_file_size / 1048576:.1f} MB"
    max_file_size_mb.short_description = 'Max Size'


@admin.register(GrantDocument)
class GrantDocumentAdmin(admin.ModelAdmin):
    list_display = ('application', 'document_type', 'original_filename', 'file_size_mb', 'verified', 'uploaded_at')
    list_filter = ('document_type', 'verified', 'uploaded_at')
    search_fields = ('application__full_name', 'application__organization_name', 'original_filename')
    readonly_fields = ('original_filename', 'file_size', 'uploaded_at')
    actions = ['mark_verified', 'mark_unverified']
    
    def file_size_mb(self, obj):
        return f"{obj.file_size / 1048576:.2f} MB"
    file_size_mb.short_description = 'Size'
    
    def mark_verified(self, request, queryset):
        updated = queryset.update(verified=True)
        self.message_user(request, f"Marked {updated} documents as verified")
    mark_verified.short_description = 'Mark as verified'
    
    def mark_unverified(self, request, queryset):
        updated = queryset.update(verified=False)
        self.message_user(request, f"Marked {updated} documents as unverified")
    mark_unverified.short_description = 'Mark as unverified'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('application', 'sender', 'subject', 'message_type', 'is_read', 'is_internal', 'created_at')
    list_filter = ('message_type', 'is_read', 'is_internal', 'created_at')
    search_fields = ('application__full_name', 'sender__username', 'subject', 'content')
    readonly_fields = ('created_at',)
    actions = ['mark_read', 'mark_unread']
    
    def mark_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"Marked {updated} messages as read")
    mark_read.short_description = 'Mark as read'
    
    def mark_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"Marked {updated} messages as unread")
    mark_unread.short_description = 'Mark as unread'


class SuccessStoryImageInline(admin.TabularInline):
    model = SuccessStoryImage
    extra = 1
    fields = ('image', 'caption', 'alt_text', 'is_primary')
    readonly_fields = ('uploaded_at',)

@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'application', 'image_count', 'is_featured', 'is_public', 'created_at')
    list_filter = ('is_featured', 'is_public', 'created_at')
    search_fields = ('title', 'story', 'application__full_name')
    actions = ['mark_featured', 'mark_public', 'mark_private']
    inlines = [SuccessStoryImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('application', 'title', 'story')
        }),
        ('Impact Details', {
            'fields': ('impact_description', 'metrics', 'video_url')
        }),
        ('Visibility Settings', {
            'fields': ('is_featured', 'is_public')
        }),
    )
    
    def image_count(self, obj):
        count = obj.images.count()
        if count > 0:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">{} image{}</span>',
                count,
                's' if count != 1 else ''
            )
        return format_html('<span style="color: #6c757d;">No images</span>')
    image_count.short_description = 'Images'
    
    def mark_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"Marked {updated} stories as featured")
    mark_featured.short_description = 'Mark as featured'
    
    def mark_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f"Made {updated} stories public")
    mark_public.short_description = 'Make public'
    
    def mark_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f"Made {updated} stories private")
    mark_private.short_description = 'Make private'

@admin.register(SuccessStoryImage)
class SuccessStoryImageAdmin(admin.ModelAdmin):
    list_display = ('success_story', 'image_preview', 'caption', 'is_primary', 'uploaded_at')
    list_filter = ('is_primary', 'uploaded_at')
    search_fields = ('success_story__title', 'caption')
    readonly_fields = ('uploaded_at', 'image_preview')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 4px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(ProgressReport)
class ProgressReportAdmin(admin.ModelAdmin):
    list_display = ('application', 'report_period', 'funds_used', 'remaining_funds', 'approved', 'submitted_date')
    list_filter = ('approved', 'submitted_date', 'reviewed_date')
    search_fields = ('application__full_name', 'application__organization_name', 'report_period')
    readonly_fields = ('submitted_date',)
    actions = ['approve_reports', 'reject_reports']
    
    def approve_reports(self, request, queryset):
        updated = queryset.update(approved=True, reviewed_date=timezone.now())
        self.message_user(request, f"Approved {updated} progress reports")
    approve_reports.short_description = 'Approve reports'
    
    def reject_reports(self, request, queryset):
        updated = queryset.update(approved=False, reviewed_date=timezone.now())
        self.message_user(request, f"Rejected {updated} progress reports")
    reject_reports.short_description = 'Reject reports'


@admin.register(FundDisbursement)
class FundDisbursementAdmin(admin.ModelAdmin):
    list_display = ('application', 'amount', 'disbursement_method', 'reference_number', 'disbursed_date', 'processed_by')
    list_filter = ('disbursement_method', 'disbursed_date', 'processed_by')
    search_fields = ('application__full_name', 'reference_number')
    readonly_fields = ('processed_by',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.processed_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ExpenseReport)
class ExpenseReportAdmin(admin.ModelAdmin):
    list_display = ('application', 'reporting_period', 'total_expenses', 'receipts_uploaded', 'submitted_date', 'approved_by')
    list_filter = ('receipts_uploaded', 'submitted_date', 'approved_date', 'approved_by')
    search_fields = ('application__full_name', 'reporting_period')
    readonly_fields = ('submitted_date',)
    actions = ['approve_expenses', 'reject_expenses']
    
    def approve_expenses(self, request, queryset):
        updated = 0
        for expense in queryset:
            expense.approved_date = timezone.now()
            expense.approved_by = request.user
            expense.save()
            updated += 1
        self.message_user(request, f"Approved {updated} expense reports")
    approve_expenses.short_description = 'Approve expense reports'
    
    def reject_expenses(self, request, queryset):
        updated = queryset.update(approved_date=None, approved_by=None)
        self.message_user(request, f"Rejected {updated} expense reports")
    reject_expenses.short_description = 'Reject expense reports'


@admin.register(GrantAnalytics)
class GrantAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_applications', 'approved_applications', 'approval_rate', 'total_amount_approved', 'avg_processing_time')
    list_filter = ('date',)
    readonly_fields = ('date',)
    ordering = ('-date',)
    
    def approval_rate(self, obj):
        if obj.total_applications > 0:
            rate = (obj.approved_applications / obj.total_applications) * 100
            return f"{rate:.1f}%"
        return "0%"
    approval_rate.short_description = 'Approval Rate'
    
    def has_add_permission(self, request):
        return False  # Analytics are generated automatically
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'object_type', 'description', 'timestamp')
    list_filter = ('action_type', 'object_type', 'timestamp')
    search_fields = ('user__username', 'description', 'object_id')
    readonly_fields = ('user', 'action_type', 'object_type', 'object_id', 'description', 'ip_address', 'user_agent', 'timestamp', 'additional_data')
    
    def has_add_permission(self, request):
        return False  # Audit logs are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should not be modified
    
    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs should not be deleted


@admin.register(GrantSettings)
class GrantSettingsAdmin(admin.ModelAdmin):
    list_display = ('approval_deadline_hours', 'processing_time_weeks_min', 'processing_time_weeks_max', 'review_frequency', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Timeline Configuration', {
            'fields': ('approval_deadline_hours', 'processing_time_weeks_min', 'processing_time_weeks_max', 'review_frequency')
        }),
        ('Welcome Message', {
            'fields': ('welcome_message',)
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        if GrantSettings.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return False  # Don't allow deletion of settings
