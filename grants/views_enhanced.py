from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, Case, When, DecimalField
from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import json
from datetime import datetime, timedelta

from .models import (
    GrantApplication, DocumentType, GrantDocument, Message, 
    SuccessStory, ProgressReport, ExpenseReport, FundDisbursement,
    GrantAnalytics, AuditLog
)
from .forms_enhanced import (
    MultiStageApplicationForm, DocumentUploadForm, MessageForm,
    SuccessStoryForm, ProgressReportForm, ExpenseReportForm,
    EligibilityScreeningForm, InterviewSchedulingForm
)

# Multi-Stage Application Views

@login_required
def eligibility_screening(request):
    """Initial eligibility screening"""
    if request.method == 'POST':
        form = EligibilityScreeningForm(request.POST)
        if form.is_valid():
            # Create or update draft application
            application, created = GrantApplication.objects.get_or_create(
                user=request.user,
                defaults={'current_stage': 'eligibility'}
            )
            
            if not created and application.current_stage != 'draft':
                messages.error(request, 'You already have an application in progress.')
                return redirect('grants:status')
            
            application.current_stage = 'eligibility'
            application.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action_type='application_created',
                object_type='GrantApplication',
                object_id=str(application.id),
                description='Passed eligibility screening'
            )
            
            messages.success(request, 'Eligibility confirmed! You can now proceed with your application.')
            return redirect('grants:application_details')
        else:
            messages.error(request, 'Please meet all eligibility requirements to proceed.')
    else:
        form = EligibilityScreeningForm()
    
    return render(request, 'grants/eligibility.html', {'form': form})

@login_required
def application_details(request):
    """Detailed application form"""
    try:
        application = GrantApplication.objects.get(user=request.user)
        if application.current_stage not in ['eligibility', 'details']:
            messages.info(request, 'This stage has already been completed.')
            return redirect('grants:status')
    except GrantApplication.DoesNotExist:
        messages.error(request, 'Please complete eligibility screening first.')
        return redirect('grants:eligibility')
    
    if request.method == 'POST':
        form = MultiStageApplicationForm(request.POST, instance=application)
        if form.is_valid():
            application = form.save(commit=False)
            application.current_stage = 'documents'
            application.save()
            
            messages.success(request, 'Application details saved! Please upload required documents.')
            return redirect('grants:document_upload')
    else:
        form = MultiStageApplicationForm(instance=application)
    
    return render(request, 'grants/application_details.html', {
        'form': form,
        'application': application
    })

@login_required
def document_upload(request):
    """Document upload stage"""
    try:
        application = GrantApplication.objects.get(user=request.user)
        if application.current_stage not in ['details', 'documents']:
            messages.info(request, 'Please complete previous stages first.')
            return redirect('grants:status')
    except GrantApplication.DoesNotExist:
        messages.error(request, 'No application found.')
        return redirect('grants:eligibility')
    
    document_types = DocumentType.objects.all().order_by('display_order')
    uploaded_documents = GrantDocument.objects.filter(application=application)
    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.application = application
            document.save()
            
            messages.success(request, f'Document "{document.document_type.name}" uploaded successfully.')
            
            # Check if all required documents are uploaded
            required_types = DocumentType.objects.filter(required=True)
            uploaded_types = uploaded_documents.values_list('document_type', flat=True)
            
            if all(doc_type.id in uploaded_types for doc_type in required_types):
                application.documents_complete = True
                application.current_stage = 'review'
                application.save()
                messages.success(request, 'All required documents uploaded! Your application is now under review.')
                return redirect('grants:status')
            
            return redirect('grants:document_upload')
    else:
        form = DocumentUploadForm()
    
    return render(request, 'grants/document_upload.html', {
        'form': form,
        'document_types': document_types,
        'uploaded_documents': uploaded_documents,
        'application': application
    })

@login_required
def interview_scheduling(request):
    """Interview scheduling"""
    try:
        application = GrantApplication.objects.get(user=request.user)
        if application.current_stage != 'interview':
            messages.info(request, 'Interview scheduling is not available at this time.')
            return redirect('grants:status')
    except GrantApplication.DoesNotExist:
        messages.error(request, 'No application found.')
        return redirect('grants:status')
    
    if request.method == 'POST':
        form = InterviewSchedulingForm(request.POST)
        if form.is_valid():
            # Save interview preferences (you might want to create a separate model for this)
            application.interview_scheduled = True
            application.save()
            
            # Send notification to admins
            admin_message = f"""
            Interview requested for: {application.full_name}
            Application ID: {application.id}
            
            Preferences:
            1. {form.cleaned_data['preferred_date_1']}
            2. {form.cleaned_data['preferred_date_2']}
            3. {form.cleaned_data['preferred_date_3']}
            
            Method: {form.cleaned_data['interview_type']}
            Special Requirements: {form.cleaned_data['special_requirements']}
            """
            
            send_mail(
                'Interview Scheduling Request',
                admin_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=True
            )
            
            messages.success(request, 'Interview scheduling request submitted. We will contact you soon.')
            return redirect('grants:status')
    else:
        form = InterviewSchedulingForm()
    
    return render(request, 'grants/interview_scheduling.html', {
        'form': form,
        'application': application
    })

# Communication Views

@login_required
def messages_view(request):
    """View and send messages"""
    try:
        application = GrantApplication.objects.get(user=request.user)
    except GrantApplication.DoesNotExist:
        messages.error(request, 'No application found.')
        return redirect('grants:eligibility')
    
    message_list = Message.objects.filter(
        application=application,
        is_internal=False
    ).order_by('-created_at')
    
    paginator = Paginator(message_list, 10)
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.application = application
            message.sender = request.user
            message.save()
            
            messages.success(request, 'Message sent successfully.')
            return redirect('grants:messages')
    else:
        form = MessageForm()
    
    return render(request, 'grants/messages.html', {
        'form': form,
        'messages': messages_page,
        'application': application
    })

# Post-Approval Views

@login_required
def grant_recipient_portal(request):
    """Main portal for approved grant recipients"""
    try:
        application = GrantApplication.objects.get(user=request.user)
        if application.status != 'approved':
            messages.error(request, 'This portal is only available for approved grants.')
            return redirect('grants:status')
    except GrantApplication.DoesNotExist:
        messages.error(request, 'No application found.')
        return redirect('grants:status')
    
    # Get recent activity
    disbursements = FundDisbursement.objects.filter(application=application).order_by('-disbursed_date')[:5]
    progress_reports = ProgressReport.objects.filter(application=application).order_by('-submitted_date')[:5]
    expense_reports = ExpenseReport.objects.filter(application=application).order_by('-submitted_date')[:5]
    
    # Calculate totals
    total_disbursed = disbursements.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expense_reports.aggregate(Sum('total_expenses'))['total_expenses__sum'] or 0
    
    context = {
        'application': application,
        'disbursements': disbursements,
        'progress_reports': progress_reports,
        'expense_reports': expense_reports,
        'total_disbursed': total_disbursed,
        'total_expenses': total_expenses,
        'remaining_funds': total_disbursed - total_expenses
    }
    
    return render(request, 'grants/recipient_portal.html', context)

@login_required
def submit_progress_report(request):
    """Submit progress report"""
    try:
        application = GrantApplication.objects.get(user=request.user, status='approved')
    except GrantApplication.DoesNotExist:
        messages.error(request, 'Only approved grant recipients can submit progress reports.')
        return redirect('grants:status')
    
    if request.method == 'POST':
        form = ProgressReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.application = application
            report.save()
            
            messages.success(request, 'Progress report submitted successfully.')
            return redirect('grants:recipient_portal')
    else:
        form = ProgressReportForm()
    
    return render(request, 'grants/progress_report.html', {
        'form': form,
        'application': application
    })

@login_required
def submit_expense_report(request):
    """Submit expense report"""
    try:
        application = GrantApplication.objects.get(user=request.user, status='approved')
    except GrantApplication.DoesNotExist:
        messages.error(request, 'Only approved grant recipients can submit expense reports.')
        return redirect('grants:status')
    
    if request.method == 'POST':
        form = ExpenseReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.application = application
            report.save()
            
            messages.success(request, 'Expense report submitted successfully.')
            return redirect('grants:recipient_portal')
    else:
        form = ExpenseReportForm()
    
    return render(request, 'grants/expense_report.html', {
        'form': form,
        'application': application
    })

@login_required
def submit_success_story(request):
    """Submit success story"""
    try:
        application = GrantApplication.objects.get(user=request.user, status='approved')
    except GrantApplication.DoesNotExist:
        messages.error(request, 'Only approved grant recipients can submit success stories.')
        return redirect('grants:status')
    
    try:
        success_story = SuccessStory.objects.get(application=application)
        edit_mode = True
    except SuccessStory.DoesNotExist:
        success_story = None
        edit_mode = False
    
    if request.method == 'POST':
        form = SuccessStoryForm(request.POST, instance=success_story)
        if form.is_valid():
            story = form.save(commit=False)
            if not edit_mode:
                story.application = application
            story.save()
            
            action = 'updated' if edit_mode else 'submitted'
            messages.success(request, f'Success story {action} successfully.')
            return redirect('grants:recipient_portal')
    else:
        form = SuccessStoryForm(instance=success_story)
    
    return render(request, 'grants/success_story.html', {
        'form': form,
        'application': application,
        'edit_mode': edit_mode
    })

# Community Views

def success_stories_public(request):
    """Public success stories page"""
    featured_stories = SuccessStory.objects.filter(
        is_public=True, 
        is_featured=True
    ).order_by('-created_at')[:3]
    
    all_stories = SuccessStory.objects.filter(is_public=True).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        all_stories = all_stories.filter(
            Q(title__icontains=search_query) |
            Q(story__icontains=search_query) |
            Q(application__project_category__icontains=search_query)
        )
    
    paginator = Paginator(all_stories, 6)
    page_number = request.GET.get('page')
    stories_page = paginator.get_page(page_number)
    
    return render(request, 'grants/success_stories.html', {
        'featured_stories': featured_stories,
        'stories': stories_page,
        'search_query': search_query
    })

# Analytics and Dashboard Views

@login_required
def analytics_dashboard(request):
    """Analytics dashboard for staff"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('grants:status')
    
    # Basic statistics
    total_applications = GrantApplication.objects.count()
    approved_applications = GrantApplication.objects.filter(status='approved').count()
    pending_applications = GrantApplication.objects.filter(status='pending').count()
    total_amount_approved = GrantApplication.objects.filter(status='approved').aggregate(
        Sum('approved_amount'))['approved_amount__sum'] or 0
    
    # Recent activity
    recent_applications = GrantApplication.objects.order_by('-created_at')[:10]
    recent_documents = GrantDocument.objects.order_by('-uploaded_at')[:10]
    
    # Category breakdown
    category_stats = GrantApplication.objects.values('project_category').annotate(
        count=Count('id'),
        total_amount=Sum('approved_amount')
    ).order_by('-count')
    
    # Stage distribution
    stage_stats = GrantApplication.objects.values('current_stage').annotate(
        count=Count('id')
    ).order_by('current_stage')
    
    context = {
        'total_applications': total_applications,
        'approved_applications': approved_applications,
        'pending_applications': pending_applications,
        'total_amount_approved': total_amount_approved,
        'approval_rate': (approved_applications / total_applications * 100) if total_applications > 0 else 0,
        'recent_applications': recent_applications,
        'recent_documents': recent_documents,
        'category_stats': category_stats,
        'stage_stats': stage_stats,
    }
    
    return render(request, 'grants/analytics_dashboard.html', context)

# AJAX Views

@require_http_methods(["GET"])
def get_application_progress(request):
    """AJAX endpoint for application progress"""
    try:
        application = GrantApplication.objects.get(user=request.user)
        return JsonResponse({
            'current_stage': application.current_stage,
            'progress_percentage': application.get_progress_percentage(),
            'status': application.status
        })
    except GrantApplication.DoesNotExist:
        return JsonResponse({'error': 'No application found'}, status=404)

@require_http_methods(["POST"])
@login_required
def mark_messages_read(request):
    """Mark messages as read"""
    message_ids = request.POST.getlist('message_ids')
    try:
        application = GrantApplication.objects.get(user=request.user)
        updated = Message.objects.filter(
            application=application,
            id__in=message_ids
        ).update(is_read=True)
        return JsonResponse({'updated': updated})
    except GrantApplication.DoesNotExist:
        return JsonResponse({'error': 'No application found'}, status=404)

@require_http_methods(["GET"])
@login_required
def get_document_status(request):
    """Get document upload status"""
    try:
        application = GrantApplication.objects.get(user=request.user)
        required_docs = DocumentType.objects.filter(required=True)
        uploaded_docs = GrantDocument.objects.filter(application=application)
        
        status = []
        for doc_type in required_docs:
            uploaded = uploaded_docs.filter(document_type=doc_type).exists()
            verified = uploaded_docs.filter(document_type=doc_type, verified=True).exists()
            status.append({
                'type': doc_type.name,
                'uploaded': uploaded,
                'verified': verified
            })
        
        return JsonResponse({'documents': status})
    except GrantApplication.DoesNotExist:
        return JsonResponse({'error': 'No application found'}, status=404)

# Additional views for complete functionality

@login_required
def application_review(request):
    """Review application before submission"""
    try:
        application = GrantApplication.objects.get(user=request.user)
        documents = GrantDocument.objects.filter(application=application)
        
        context = {
            'application': application,
            'documents': documents,
        }
        return render(request, 'grants/application_review.html', context)
    except GrantApplication.DoesNotExist:
        messages.error(request, 'No application found.')
        return redirect('grants:eligibility')

@require_http_methods(["POST"])
@login_required
def upload_document(request):
    """Handle document upload via AJAX"""
    try:
        application = GrantApplication.objects.get(user=request.user)
        document_type_id = request.POST.get('document_type_id')
        document_type = DocumentType.objects.get(id=document_type_id)
        
        if 'document' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file provided'})
        
        file = request.FILES['document']
        
        # Validate file size (10MB)
        if file.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File size exceeds 10MB limit'})
        
        # Create or update document
        document, created = GrantDocument.objects.get_or_create(
            application=application,
            document_type=document_type,
            defaults={'file': file, 'uploaded_by': request.user}
        )
        
        if not created:
            # Update existing document
            document.file = file
            document.uploaded_by = request.user
            document.verified = False  # Reset verification status
            document.save()
        
        # Log the upload
        AuditLog.objects.create(
            application=application,
            action='document_uploaded',
            details=f'Uploaded {document_type.name}',
            user=request.user
        )
        
        return JsonResponse({'success': True, 'message': 'Document uploaded successfully'})
        
    except (GrantApplication.DoesNotExist, DocumentType.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["POST"])
@login_required
def update_application_stage(request):
    """Update application stage via AJAX"""
    try:
        application = GrantApplication.objects.get(user=request.user)
        data = json.loads(request.body)
        stage = data.get('stage')
        
        if stage in dict(GrantApplication.APPLICATION_STAGES):
            application.current_stage = stage
            application.save()
            
            # Log the stage change
            AuditLog.objects.create(
                application=application,
                action='stage_updated',
                details=f'Stage updated to {stage}',
                user=request.user
            )
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid stage'})
            
    except GrantApplication.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No application found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def recipient_portal(request):
    """Main recipient portal view"""
    try:
        application = GrantApplication.objects.get(user=request.user, status='approved')
        
        # Get financial data
        disbursements = FundDisbursement.objects.filter(application=application)
        expense_reports = ExpenseReport.objects.filter(application=application)
        progress_reports = ProgressReport.objects.filter(application=application)
        messages = Message.objects.filter(application=application).order_by('-created_at')
        
        total_disbursed = disbursements.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        remaining_amount = application.approved_amount - total_disbursed
        utilization_percentage = (total_disbursed / application.approved_amount * 100) if application.approved_amount > 0 else 0
        
        unread_messages_count = messages.filter(is_read=False).count()
        reports_due_count = 1 if progress_reports.count() == 0 else 0  # Simplified logic
        
        context = {
            'application': application,
            'disbursements': disbursements,
            'expense_reports': expense_reports,
            'progress_reports': progress_reports,
            'messages': messages[:10],  # Latest 10 messages
            'total_disbursed': total_disbursed,
            'remaining_amount': remaining_amount,
            'utilization_percentage': utilization_percentage,
            'unread_messages_count': unread_messages_count,
            'reports_due_count': reports_due_count,
        }
        
        return render(request, 'grants/recipient_portal.html', context)
        
    except GrantApplication.DoesNotExist:
        messages.error(request, 'Access denied. You do not have an approved grant.')
        return redirect('grants:status')

@require_http_methods(["POST"])
@login_required
def send_message(request):
    """Send a message"""
    try:
        application = GrantApplication.objects.get(user=request.user)
        
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        reply_to_id = request.POST.get('reply_to')
        
        if not subject or not content:
            messages.error(request, 'Subject and message content are required.')
            return redirect('grants:messages')
        
        message = Message.objects.create(
            application=application,
            sender=request.user,
            subject=subject,
            content=content,
            reply_to_id=reply_to_id if reply_to_id else None
        )
        
        # Handle attachment if provided
        if 'attachment' in request.FILES:
            message.attachment = request.FILES['attachment']
            message.save()
        
        messages.success(request, 'Message sent successfully.')
        return redirect('grants:messages')
        
    except GrantApplication.DoesNotExist:
        messages.error(request, 'No application found.')
        return redirect('grants:apply')

@require_http_methods(["GET"])
@login_required
def get_message(request):
    """Get message details for reply"""
    try:
        message_id = request.GET.get('id')
        message = Message.objects.get(id=message_id)
        
        # Check permission
        if message.application.user != request.user and not request.user.is_staff:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        return JsonResponse({
            'subject': message.subject,
            'content': message.content,
            'sender_name': message.sender.get_full_name() if message.sender else 'Grant Administrator'
        })
        
    except Message.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)

@require_http_methods(["POST"])
@login_required
def delete_message(request):
    """Delete a message"""
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        message = Message.objects.get(id=message_id)
        
        # Check permission
        if message.application.user != request.user and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'Access denied'})
        
        message.delete()
        return JsonResponse({'success': True})
        
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message not found'})

@require_http_methods(["GET"])
@login_required
def get_unread_count(request):
    """Get unread messages count"""
    try:
        application = GrantApplication.objects.get(user=request.user)
        count = Message.objects.filter(
            application=application,
            is_read=False
        ).count()
        return JsonResponse({'count': count})
        
    except GrantApplication.DoesNotExist:
        return JsonResponse({'count': 0})

@login_required
def success_stories(request):
    """Public success stories view with filtering and search"""
    stories = SuccessStory.objects.filter(approved=True).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        stories = stories.filter(
            Q(title__icontains=search_query) |
            Q(story_text__icontains=search_query) |
            Q(applicant__full_name__icontains=search_query)
        )
    
    # Category filtering
    category = request.GET.get('category', '')
    if category:
        stories = stories.filter(category=category)
    
    # Pagination
    paginator = Paginator(stories, 9)  # 9 stories per page
    page_number = request.GET.get('page')
    stories_page = paginator.get_page(page_number)
    
    # Get categories for filter dropdown
    categories = SuccessStory.objects.filter(approved=True).values_list('category', flat=True).distinct()
    
    context = {
        'stories': stories_page,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category,
    }
    
    return render(request, 'grants/success_stories.html', context)

@login_required
def submit_success_story(request):
    """Submit a success story"""
    try:
        application = GrantApplication.objects.get(user=request.user, status='approved')
    except GrantApplication.DoesNotExist:
        messages.error(request, 'Only approved grant recipients can submit success stories.')
        return redirect('grants:status')
    
    if request.method == 'POST':
        form = SuccessStoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.applicant = request.user
            story.application = application
            story.save()
            
            # Send notification to administrators
            try:
                send_mail(
                    subject='New Success Story Submitted',
                    message=f'A new success story has been submitted by {application.full_name}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin[1] for admin in settings.ADMINS],
                    fail_silently=True
                )
            except Exception:
                pass
            
            messages.success(request, 'Your success story has been submitted for review. Thank you for sharing!')
            return redirect('grants:recipient_portal')
    else:
        form = SuccessStoryForm()
    
    context = {
        'form': form,
        'application': application,
    }
    
    return render(request, 'grants/submit_success_story.html', context)

@login_required
def community_dashboard(request):
    """Community engagement dashboard"""
    # Get community statistics
    total_stories = SuccessStory.objects.filter(approved=True).count()
    total_impact_amount = GrantApplication.objects.filter(
        status='approved'
    ).aggregate(total=Sum('approved_amount'))['total'] or 0
    
    # Recent success stories
    recent_stories = SuccessStory.objects.filter(
        approved=True
    ).order_by('-created_at')[:6]
    
    # Impact metrics
    total_recipients = GrantApplication.objects.filter(status='approved').count()
    average_grant = GrantApplication.objects.filter(
        status='approved'
    ).aggregate(avg=Avg('approved_amount'))['avg'] or 0
    
    # Featured story (most recent or manually featured)
    featured_story = SuccessStory.objects.filter(
        approved=True,
        featured=True
    ).first() or recent_stories.first() if recent_stories else None
    
    context = {
        'total_stories': total_stories,
        'total_impact_amount': total_impact_amount,
        'total_recipients': total_recipients,
        'average_grant': average_grant,
        'recent_stories': recent_stories,
        'featured_story': featured_story,
    }
    
    return render(request, 'grants/community_dashboard.html', context)

# Financial Management Integration

@staff_member_required
def financial_dashboard(request):
    """Financial management dashboard for administrators"""
    # Get financial overview
    total_approved_funding = GrantApplication.objects.filter(
        status='approved'
    ).aggregate(total=Sum('approved_amount'))['total'] or 0
    
    total_disbursed = FundDisbursement.objects.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    pending_disbursements = FundDisbursement.objects.filter(
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_expenses = ExpenseReport.objects.filter(
        status='approved'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent financial activity
    recent_disbursements = FundDisbursement.objects.order_by('-disbursement_date')[:10]
    recent_expenses = ExpenseReport.objects.order_by('-created_at')[:10]
    pending_expense_reports = ExpenseReport.objects.filter(status='pending').count()
    
    # Monthly financial trends
    monthly_disbursements = []
    monthly_labels = []
    
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_disbursed = FundDisbursement.objects.filter(
            disbursement_date__gte=month_start,
            disbursement_date__lte=month_end,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_labels.insert(0, month_start.strftime('%b %Y'))
        monthly_disbursements.insert(0, float(month_disbursed))
    
    context = {
        'total_approved_funding': total_approved_funding,
        'total_disbursed': total_disbursed,
        'pending_disbursements': pending_disbursements,
        'total_expenses': total_expenses,
        'remaining_funding': total_approved_funding - total_disbursed,
        'utilization_rate': (total_disbursed / max(total_approved_funding, 1)) * 100,
        'recent_disbursements': recent_disbursements,
        'recent_expenses': recent_expenses,
        'pending_expense_reports': pending_expense_reports,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_disbursements': json.dumps(monthly_disbursements),
    }
    
    return render(request, 'grants/financial_dashboard.html', context)

@staff_member_required
def process_disbursement(request, application_id):
    """Process a disbursement for an approved application"""
    application = get_object_or_404(GrantApplication, id=application_id, status='approved')
    
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        purpose = request.POST.get('purpose', '')
        method = request.POST.get('method', 'bank_transfer')
        
        if amount <= 0:
            messages.error(request, 'Invalid disbursement amount.')
            return redirect('grants:financial_dashboard')
        
        # Check if total disbursements would exceed approved amount
        total_disbursed = FundDisbursement.objects.filter(
            application=application
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if total_disbursed + amount > application.approved_amount:
            messages.error(request, 'Disbursement amount exceeds remaining grant balance.')
            return redirect('grants:financial_dashboard')
        
        # Create disbursement record
        disbursement = FundDisbursement.objects.create(
            application=application,
            amount=amount,
            purpose=purpose,
            method=method,
            disbursement_date=timezone.now(),
            processed_by=request.user,
            status='completed'  # In real implementation, this might be 'pending' initially
        )
        
        # Log the disbursement
        AuditLog.objects.create(
            application=application,
            action='disbursement_processed',
            details=f'Disbursed ${amount} for {purpose}',
            user=request.user
        )
        
        # Send notification to recipient
        try:
            send_mail(
                subject='Grant Funds Disbursed',
                message=f'Your grant funds of ${amount} have been disbursed for {purpose}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                fail_silently=True
            )
        except Exception:
            pass
        
        messages.success(request, f'Disbursement of ${amount} processed successfully.')
        return redirect('grants:financial_dashboard')
    
    context = {
        'application': application,
        'total_disbursed': FundDisbursement.objects.filter(
            application=application
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    return render(request, 'grants/process_disbursement.html', context)

@login_required
def submit_expense_report(request):
    """Submit an expense report"""
    try:
        application = GrantApplication.objects.get(user=request.user, status='approved')
    except GrantApplication.DoesNotExist:
        messages.error(request, 'Only approved grant recipients can submit expense reports.')
        return redirect('grants:status')
    
    if request.method == 'POST':
        form = ExpenseReportForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.application = application
            expense.submitted_by = request.user
            expense.save()
            
            # Log the expense submission
            AuditLog.objects.create(
                application=application,
                action='expense_submitted',
                details=f'Expense report for ${expense.amount} - {expense.description[:50]}',
                user=request.user
            )
            
            # Notify administrators
            try:
                send_mail(
                    subject='New Expense Report Submitted',
                    message=f'New expense report submitted by {application.full_name} for ${expense.amount}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin[1] for admin in settings.ADMINS],
                    fail_silently=True
                )
            except Exception:
                pass
            
            messages.success(request, 'Expense report submitted successfully.')
            return redirect('grants:recipient_portal')
    else:
        form = ExpenseReportForm()
    
    context = {
        'form': form,
        'application': application,
    }
    
    return render(request, 'grants/submit_expense_report.html', context)

@login_required
def submit_progress_report(request):
    """Submit a progress report"""
    try:
        application = GrantApplication.objects.get(user=request.user, status='approved')
    except GrantApplication.DoesNotExist:
        messages.error(request, 'Only approved grant recipients can submit progress reports.')
        return redirect('grants:status')
    
    if request.method == 'POST':
        form = ProgressReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.application = application
            report.submitted_by = request.user
            report.save()
            
            # Log the progress report submission
            AuditLog.objects.create(
                application=application,
                action='progress_report_submitted',
                details=f'Progress report submitted for period {report.report_period_start} to {report.report_period_end}',
                user=request.user
            )
            
            # Notify administrators
            try:
                send_mail(
                    subject='New Progress Report Submitted',
                    message=f'New progress report submitted by {application.full_name}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin[1] for admin in settings.ADMINS],
                    fail_silently=True
                )
            except Exception:
                pass
            
            messages.success(request, 'Progress report submitted successfully.')
            return redirect('grants:recipient_portal')
    else:
        form = ProgressReportForm()
    
    context = {
        'form': form,
        'application': application,
    }
    
    return render(request, 'grants/submit_progress_report.html', context)

# Enhanced Security & Compliance

@staff_member_required
def security_dashboard(request):
    """Security and compliance dashboard"""
    # Recent audit activities
    recent_audits = AuditLog.objects.order_by('-timestamp')[:50]
    
    # Security metrics
    total_logins_today = AuditLog.objects.filter(
        timestamp__date=timezone.now().date(),
        action='user_login'
    ).count()
    
    failed_login_attempts = AuditLog.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=7),
        action='failed_login'
    ).count()
    
    suspicious_activities = AuditLog.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=30),
        action__in=['unauthorized_access', 'data_breach_attempt', 'suspicious_activity']
    ).count()
    
    # Data integrity checks
    applications_with_missing_data = GrantApplication.objects.filter(
        Q(full_name__isnull=True) | Q(full_name='') |
        Q(email__isnull=True) | Q(email='') |
        Q(amount_requested__isnull=True)
    ).count()
    
    # Compliance metrics
    overdue_reports = ProgressReport.objects.filter(
        report_period_end__lt=timezone.now() - timedelta(days=30),
        status='pending'
    ).count()
    
    unverified_documents = GrantDocument.objects.filter(
        verified=False,
        created_at__lt=timezone.now() - timedelta(days=7)
    ).count()
    
    # Generate compliance score
    compliance_issues = (
        applications_with_missing_data +
        overdue_reports +
        unverified_documents +
        failed_login_attempts
    )
    
    total_items = (
        GrantApplication.objects.count() +
        ProgressReport.objects.count() +
        GrantDocument.objects.count() +
        100  # Base score for login attempts
    )
    
    compliance_score = max(0, 100 - (compliance_issues / max(total_items, 1)) * 100)
    
    context = {
        'recent_audits': recent_audits,
        'total_logins_today': total_logins_today,
        'failed_login_attempts': failed_login_attempts,
        'suspicious_activities': suspicious_activities,
        'applications_with_missing_data': applications_with_missing_data,
        'overdue_reports': overdue_reports,
        'unverified_documents': unverified_documents,
        'compliance_score': round(compliance_score, 1),
    }
    
    return render(request, 'grants/security_dashboard.html', context)

@staff_member_required
def audit_log_view(request):
    """Detailed audit log view with filtering"""
    logs = AuditLog.objects.all().order_by('-timestamp')
    
    # Filtering
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    user_filter = request.GET.get('user', '')
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    date_from = request.GET.get('date_from', '')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    
    date_to = request.GET.get('date_to', '')
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    logs_page = paginator.get_page(page_number)
    
    # Get available actions for filter dropdown
    available_actions = AuditLog.objects.values_list('action', flat=True).distinct()
    
    context = {
        'logs': logs_page,
        'available_actions': available_actions,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'grants/audit_log.html', context)

@staff_member_required
def compliance_report(request):
    """Generate compliance reports"""
    # Generate comprehensive compliance report
    report_data = {
        'generated_at': timezone.now(),
        'period_start': timezone.now() - timedelta(days=90),
        'period_end': timezone.now(),
    }
    
    # Application compliance
    total_applications = GrantApplication.objects.count()
    complete_applications = GrantApplication.objects.exclude(
        Q(full_name__isnull=True) | Q(full_name='') |
        Q(email__isnull=True) | Q(email='') |
        Q(amount_requested__isnull=True)
    ).count()
    
    # Document compliance
    total_documents = GrantDocument.objects.count()
    verified_documents = GrantDocument.objects.filter(verified=True).count()
    
    # Financial compliance
    total_disbursements = FundDisbursement.objects.count()
    documented_disbursements = FundDisbursement.objects.exclude(
        Q(purpose__isnull=True) | Q(purpose='')
    ).count()
    
    # Reporting compliance
    approved_applications = GrantApplication.objects.filter(status='approved')
    applications_with_reports = approved_applications.filter(
        progressreport__isnull=False
    ).distinct().count()
    
    report_data.update({
        'application_completion_rate': (complete_applications / max(total_applications, 1)) * 100,
        'document_verification_rate': (verified_documents / max(total_documents, 1)) * 100,
        'disbursement_documentation_rate': (documented_disbursements / max(total_disbursements, 1)) * 100,
        'progress_reporting_rate': (applications_with_reports / max(approved_applications.count(), 1)) * 100,
        'total_applications': total_applications,
        'complete_applications': complete_applications,
        'total_documents': total_documents,
        'verified_documents': verified_documents,
        'total_disbursements': total_disbursements,
        'documented_disbursements': documented_disbursements,
        'approved_applications_count': approved_applications.count(),
        'applications_with_reports': applications_with_reports,
    })
    
    # Calculate overall compliance score
    overall_compliance = (
        report_data['application_completion_rate'] +
        report_data['document_verification_rate'] +
        report_data['disbursement_documentation_rate'] +
        report_data['progress_reporting_rate']
    ) / 4
    
    report_data['overall_compliance_score'] = round(overall_compliance, 1)
    
    # Recent security events
    security_events = AuditLog.objects.filter(
        timestamp__gte=report_data['period_start'],
        action__in=['failed_login', 'unauthorized_access', 'data_breach_attempt']
    ).order_by('-timestamp')
    
    report_data['security_events'] = security_events
    report_data['security_events_count'] = security_events.count()
    
    context = {
        'report': report_data,
    }
    
    return render(request, 'grants/compliance_report.html', context)

@login_required
def submit_success_story(request):
    """Allow approved grant recipients to submit their success stories with images"""
    try:
        grant = GrantApplication.objects.get(user=request.user, status='approved')
    except GrantApplication.DoesNotExist:
        messages.error(request, "You must have an approved grant to submit a success story.")
        return redirect('grants:status')
    
    # Check if success story already exists
    success_story, created = SuccessStory.objects.get_or_create(
        application=grant,
        defaults={
            'title': f"{grant.project_title} - Success Story",
            'story': '',
            'impact_description': ''
        }
    )
    
    if request.method == 'POST':
        from .forms import SuccessStoryForm, SuccessStoryImageFormSet
        
        form = SuccessStoryForm(request.POST, instance=success_story)
        image_formset = SuccessStoryImageFormSet(
            request.POST, 
            request.FILES, 
            instance=success_story
        )
        
        if form.is_valid() and image_formset.is_valid():
            success_story = form.save()
            images = image_formset.save()
            
            messages.success(request, "Your success story has been saved! Thank you for sharing your impact.")
            return redirect('grants:view_success_story', story_id=success_story.id)
    else:
        from .forms import SuccessStoryForm, SuccessStoryImageFormSet
        
        form = SuccessStoryForm(instance=success_story)
        image_formset = SuccessStoryImageFormSet(instance=success_story)
    
    return render(request, 'grants/submit_success_story.html', {
        'form': form,
        'image_formset': image_formset,
        'success_story': success_story,
        'grant': grant
    })

def view_success_story(request, story_id):
    """View an individual success story"""
    try:
        success_story = SuccessStory.objects.get(id=story_id, is_public=True)
    except SuccessStory.DoesNotExist:
        messages.error(request, "Success story not found.")
        return redirect('grants:success_stories')
    
    return render(request, 'grants/view_success_story.html', {
        'success_story': success_story
    })

def success_stories_list(request):
    """Display paginated list of public success stories with filtering"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from decimal import Decimal
    
    # Get filter parameters
    search = request.GET.get('search', '')
    amount_range = request.GET.get('amount_range', '')
    sort = request.GET.get('sort', '-created_at')
    
    # Base queryset
    stories = SuccessStory.objects.filter(is_public=True).select_related('application')
    
    # Apply search filter
    if search:
        stories = stories.filter(
            Q(title__icontains=search) |
            Q(story__icontains=search) |
            Q(application__organization_name__icontains=search) |
            Q(application__project_title__icontains=search)
        )
    
    # Apply amount range filter
    if amount_range:
        if amount_range == '0-10000':
            stories = stories.filter(
                Q(application__approved_amount__lt=10000) |
                Q(application__approved_amount__isnull=True, application__amount_requested__lt=10000)
            )
        elif amount_range == '10000-50000':
            stories = stories.filter(
                Q(application__approved_amount__gte=10000, application__approved_amount__lt=50000) |
                Q(application__approved_amount__isnull=True, application__amount_requested__gte=10000, application__amount_requested__lt=50000)
            )
        elif amount_range == '50000-100000':
            stories = stories.filter(
                Q(application__approved_amount__gte=50000, application__approved_amount__lt=100000) |
                Q(application__approved_amount__isnull=True, application__amount_requested__gte=50000, application__amount_requested__lt=100000)
            )
        elif amount_range == '100000+':
            stories = stories.filter(
                Q(application__approved_amount__gte=100000) |
                Q(application__approved_amount__isnull=True, application__amount_requested__gte=100000)
            )
    
    # Apply sorting
    if sort == 'grant_amount':
        stories = stories.extra(
            select={'grant_amount': 'COALESCE(grants_grantapplication.approved_amount, grants_grantapplication.amount_requested)'}
        ).order_by('grant_amount')
    elif sort == '-grant_amount':
        stories = stories.extra(
            select={'grant_amount': 'COALESCE(grants_grantapplication.approved_amount, grants_grantapplication.amount_requested)'}
        ).order_by('-grant_amount')
    else:
        stories = stories.order_by(sort)
    
    # Calculate statistics
    total_stories = SuccessStory.objects.filter(is_public=True).count()
    total_impact = SuccessStory.objects.filter(is_public=True).aggregate(
        total=models.Sum(
            models.Case(
                models.When(application__approved_amount__isnull=False, then='application__approved_amount'),
                default='application__amount_requested',
                output_field=models.DecimalField()
            )
        )
    )['total'] or 0
    
    total_organizations = SuccessStory.objects.filter(is_public=True).values('application__organization_name').distinct().count()
    
    # Pagination
    paginator = Paginator(stories, 12)  # Show 12 stories per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'success_stories': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_stories': total_stories,
        'total_impact': total_impact,
        'total_organizations': total_organizations,
        'total_beneficiaries': 'Thousands',  # Could be calculated if you have beneficiary data
    }
    
    return render(request, 'grants/success_stories.html', context)

def log_security_event(request, action, details, application=None):
    """Helper function to log security events"""
    AuditLog.objects.create(
        application=application,
        action=action,
        details=details,
        user=request.user if request.user.is_authenticated else None,
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )

@staff_member_required
def analytics_dashboard(request):
    """Comprehensive analytics dashboard"""
    # Get date range filter
    range_days = request.GET.get('range', '30')
    if range_days == 'all':
        start_date = None
    else:
        start_date = timezone.now() - timedelta(days=int(range_days))
    
    # Base queryset
    applications = GrantApplication.objects.all()
    if start_date:
        applications = applications.filter(created_at__gte=start_date)
    
    # Calculate key metrics
    total_applications = applications.count()
    approved_applications = applications.filter(status='approved').count()
    pending_applications = applications.filter(status='pending').count()
    rejected_applications = applications.filter(status='rejected').count()
    in_progress_applications = applications.exclude(status__in=['approved', 'pending', 'rejected']).count()
    
    # Financial metrics
    total_funding = applications.filter(status='approved').aggregate(
        total=Sum('approved_amount')
    )['total'] or 0
    
    avg_grant_amount = applications.filter(status='approved').aggregate(
        avg=Avg('approved_amount')
    )['avg'] or 0
    
    # Processing time metrics
    approved_apps = applications.filter(status='approved', approval_date__isnull=False)
    if approved_apps.exists():
        avg_processing_time = sum([
            (app.approval_date - app.created_at).days 
            for app in approved_apps
        ]) / approved_apps.count()
    else:
        avg_processing_time = 0
    
    # Growth calculation
    if start_date:
        previous_period = applications.filter(
            created_at__lt=start_date,
            created_at__gte=start_date - timedelta(days=int(range_days))
        ).count()
        applications_growth = ((total_applications - previous_period) / max(previous_period, 1)) * 100
    else:
        applications_growth = 0
    
    # Monthly data for charts
    monthly_data = []
    monthly_labels = []
    monthly_applications = []
    monthly_approvals = []
    
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_apps = GrantApplication.objects.filter(
            created_at__gte=month_start,
            created_at__lte=month_end
        ).count()
        
        month_approvals = GrantApplication.objects.filter(
            approval_date__gte=month_start,
            approval_date__lte=month_end,
            status='approved'
        ).count()
        
        monthly_labels.insert(0, month_start.strftime('%b %Y'))
        monthly_applications.insert(0, month_apps)
        monthly_approvals.insert(0, month_approvals)
    
    # Funding distribution
    funding_ranges = [
        (0, 5000, '$0-$5K'),
        (5000, 10000, '$5K-$10K'),
        (10000, 25000, '$10K-$25K'),
        (25000, 50000, '$25K-$50K'),
        (50000, float('inf'), '$50K+')
    ]
    
    funding_distribution = []
    for min_amt, max_amt, label in funding_ranges:
        if max_amt == float('inf'):
            count = applications.filter(
                status='approved',
                approved_amount__gte=min_amt
            ).count()
        else:
            count = applications.filter(
                status='approved',
                approved_amount__gte=min_amt,
                approved_amount__lt=max_amt
            ).count()
        funding_distribution.append(count)
    
    # Geographic distribution
    geographic_data = applications.values('address').annotate(
        applications=Count('id'),
        approved=Count('id', filter=Q(status='approved')),
        funding=Sum('approved_amount', filter=Q(status='approved'))
    ).order_by('-applications')[:10]
    
    # Process geographic data to extract city/state
    for item in geographic_data:
        address_parts = item['address'].split(',') if item['address'] else ['Unknown', 'Unknown']
        if len(address_parts) >= 2:
            item['city'] = address_parts[-2].strip()
            item['state'] = address_parts[-1].strip()
        else:
            item['city'] = 'Unknown'
            item['state'] = 'Unknown'
        item['funding'] = item['funding'] or 0
    
    # Recent applications
    recent_applications = applications.order_by('-created_at')[:10]
    
    # Performance metrics
    approval_rate = (approved_applications / max(total_applications, 1)) * 100
    completion_rate = 85  # This would be calculated based on actual project completion data
    satisfaction_score = 4.2  # This would come from recipient feedback surveys
    
    analytics = {
        'total_applications': total_applications,
        'approved_applications': approved_applications,
        'pending_applications': pending_applications,
        'rejected_applications': rejected_applications,
        'in_progress_applications': in_progress_applications,
        'total_funding': total_funding,
        'avg_grant_amount': avg_grant_amount,
        'avg_processing_time': round(avg_processing_time),
        'applications_growth': round(applications_growth, 1),
        'approval_rate': round(approval_rate, 1),
        'completion_rate': completion_rate,
        'satisfaction_score': satisfaction_score,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_applications': json.dumps(monthly_applications),
        'monthly_approvals': json.dumps(monthly_approvals),
        'funding_distribution': json.dumps(funding_distribution),
        'geographic_data': geographic_data,
    }
    
    context = {
        'analytics': analytics,
        'recent_applications': recent_applications,
    }
    
    return render(request, 'grants/analytics_dashboard.html', context)

@staff_member_required
def export_analytics(request):
    """Export analytics data to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="grant_analytics.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Full Name', 'Email', 'Amount Requested', 'Approved Amount',
        'Status', 'Stage', 'Created Date', 'Approval Date', 'Address'
    ])
    
    applications = GrantApplication.objects.all().order_by('-created_at')
    for app in applications:
        writer.writerow([
            app.id,
            app.full_name,
            app.email,
            app.amount_requested,
            app.approved_amount or '',
            app.status,
            app.current_stage,
            app.created_at.strftime('%Y-%m-%d'),
            app.approval_date.strftime('%Y-%m-%d') if app.approval_date else '',
            app.address
        ])
    
    return response