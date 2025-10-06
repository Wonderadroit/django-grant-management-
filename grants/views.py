from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms_enhanced import MultiStageApplicationForm
from .models import GrantApplication, GrantSettings
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail, mail_admins
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404
from . import ai as ai_helper
from django.contrib.auth.models import User

@login_required
def dashboard(request):
    """User dashboard showing grant application overview"""
    grant = GrantApplication.objects.filter(user=request.user).last()
    
    context = {
        'grant': grant,
        'user': request.user,
    }
    
    return render(request, 'grants/dashboard.html', context)


@login_required
def apply_for_grant(request):
    # Check if user already has an application
    if GrantApplication.objects.filter(user=request.user).exists():
        grant = GrantApplication.objects.get(user=request.user)
        return render(request, "grants/already_applied.html", {"grant": grant})

    # Get grant settings for welcome message and timeline info
    try:
        grant_settings = GrantSettings.objects.first()
    except GrantSettings.DoesNotExist:
        grant_settings = None

    if request.method == "POST":
        form = MultiStageApplicationForm(request.POST)
        if form.is_valid():
            # Get email from form to check for existing applications
            email = form.cleaned_data.get('email')
            
            # Check if ANY user with this email already has an application
            existing_user_with_email = User.objects.filter(email=email).exclude(id=request.user.id).first()
            if existing_user_with_email and GrantApplication.objects.filter(user=existing_user_with_email).exists():
                messages.error(request, f'An application already exists for {email}. Each person can only submit one grant application. Please contact us if you need assistance.')
                return redirect('grants:apply')
            
            grant = form.save(commit=False)
            grant.user = request.user
            grant.current_stage = 'eligibility'  # Start with eligibility stage
            grant.save()
            
            messages.success(request, 'Application submitted successfully! You will receive approval within 24 hours, with processing and payment within 2-4 weeks.')
            
            # Send confirmation email to applicant
            try:
                context = {
                    'grant': grant,
                    'grant_settings': grant_settings,
                }
                subject = 'Grant Application Received - Dave Johnson Foundation'
                
                email_body = f'''Dear {grant.full_name},

Thank you for submitting your grant application to the Dave Johnson Foundation.

Application Details:
- Application ID: DJF-{grant.id:04d}
- Project Title: {grant.project_title}
- Amount Requested: ${grant.amount_requested:,}
- Submission Date: {grant.created_at.strftime('%B %d, %Y at %I:%M %p')}

Timeline:
✓ Application Submitted - {grant.created_at.strftime('%B %d, %Y')}
⏳ Review & Approval - Within 24 hours
⏳ Processing & Payment - 2-4 weeks after approval

What's Next:
1. We will review your application within 24 hours
2. You will receive an email notification of our decision
3. If approved, funds will be processed and disbursed within 2-4 weeks
4. You can check your application status anytime by logging into your account

Important Notes:
- Applications are reviewed monthly by our grant committee
- No additional documentation is required at this time
- We will contact you if any clarification is needed

You can check your application status at any time by logging into your account and visiting the "Check Status" page.

Thank you for your commitment to making a positive impact in your community.

Best regards,
Dave Johnson Foundation Team

---
This is an automated message. Please do not reply to this email.
For questions, please contact us through your application portal.'''

                msg = EmailMultiAlternatives(subject, email_body, settings.DEFAULT_FROM_EMAIL, [grant.email])
                msg.send(fail_silently=True)
            except Exception:
                pass
                
            # Notify admins with enhanced details
            try:
                admin_message = f'''New Grant Application Received

Applicant Details:
- Name: {grant.full_name}
- Email: {grant.email}
- Phone: {grant.phone}

Application Details:
- Application ID: DJF-{grant.id:04d}
- Project Title: {grant.project_title}
- Category: {grant.get_project_category_display()}
- Amount Requested: ${grant.amount_requested:,}
- Organization: {grant.organization_name if grant.organization_name else "Individual Application"}

Timeline Reminder:
- Review Deadline: {(grant.created_at + timedelta(hours=24)).strftime('%B %d, %Y at %I:%M %p')}
- Processing Window: 2-4 weeks after approval

Please review in the admin panel: /admin/grants/grantapplication/{grant.id}/'''
                
                mail_admins('New Grant Application - Review Required', admin_message)
            except Exception:
                pass
                
            return redirect('grants:wait')
    else:
        form = MultiStageApplicationForm()
        # Pre-populate user information if available
        if request.user.first_name or request.user.last_name:
            form.initial['full_name'] = f"{request.user.first_name} {request.user.last_name}".strip()
        if request.user.email:
            form.initial['email'] = request.user.email

    context = {
        'form': form,
        'grant_settings': grant_settings,
        'user': request.user
    }
    return render(request, "grants/apply_new.html", context)


@login_required
def wait(request):
    grant = GrantApplication.objects.filter(user=request.user).last()
    hours_remaining = None
    if grant:
        elapsed = timezone.now() - grant.created_at
        remaining = timedelta(hours=24) - elapsed  # 24-hour approval window
        hours_remaining = max(0, int(remaining.total_seconds() // 3600))
        minutes_remaining = max(0, int((remaining.total_seconds() % 3600) // 60))
    return render(request, 'grants/wait.html', {
        'grant': grant, 
        'hours_remaining': hours_remaining,
        'minutes_remaining': minutes_remaining
    })

@login_required
def check_status(request):
    grant = GrantApplication.objects.filter(user=request.user).last()
    message = "You don’t have any application yet."

    if grant:
        # Check current status from database (admin may have updated it)
        grant.refresh_from_db()
        
        # Production mode: No auto-approval - all grants require manual admin review
        # Auto-approval has been disabled for production use
        
        # Display status based on current state
        if grant.status.lower() == 'approved':
            approval_method = "approved by our team"
            message = (f"🎉 Congratulations {grant.full_name}! Your grant application has been {approval_method}.\n\n"
                       f"**Approved Amount:** ${grant.approved_amount or grant.amount_requested:,}\n"
                       f"**Approval Date:** {grant.approval_date.strftime('%B %d, %Y at %I:%M %p') if grant.approval_date else 'Recently'}\n\n"
                       "Click 'View Approval Letter' below to download your official approval document and get next steps for fund disbursement.")
        elif grant.status.lower() == 'rejected':
            message = (f"Thank you for your interest in the Dave Johnson Foundation, {grant.full_name}. "
                       f"After careful review, your application for \"{grant.project_title}\" was not selected for funding at this time.\n\n"
                       "This decision does not reflect the value of your project. Due to high volume and limited funding, "
                       "we can only approve a small percentage of requests. We encourage you to consider reapplying in future funding cycles.")
        elif grant.status.lower() == 'under_review':
            days_in_review = (timezone.now() - grant.created_at).days
            message = (f"📋 Your application is currently under review by our grant committee.\n\n"
                       f"**Application ID:** DJF-{grant.id:04d}\n"
                       f"**Days in Review:** {days_in_review}\n"
                       f"**Current Stage:** {grant.get_current_stage_display()}\n\n"
                       "We appreciate your patience. Our team carefully evaluates each application. "
                       "You will receive an email notification once a decision is made.")
        elif grant.status.lower() == 'on_hold':
            message = (f"⏸️ Your application is currently on hold.\n\n"
                       f"**Reason:** {grant.approval_notes if grant.approval_notes else 'Additional review required'}\n\n"
                       "We may need additional information or clarification. Please check your email for any requests from our team.")
        else:  # pending
            days_since_submission = (timezone.now() - grant.created_at).days
            
            message = (f"⏳ Your application is being reviewed by our grant committee.\n\n"
                       f"**Application ID:** DJF-{grant.id:04d}\n"
                       f"**Submitted:** {grant.created_at.strftime('%B %d, %Y')}\n"
                       f"**Days in Review:** {days_since_submission}\n\n"
                       "Our team carefully evaluates each application. "
                       "You will receive an email notification once a decision is made. "
                       "Thank you for your patience as we review your submission.")

    return render(request, 'grants/status.html', {"message": message, "grant": grant})


@login_required
def approval_letter(request):
    """Display the official approval letter with download and next steps"""
    grant = get_object_or_404(GrantApplication, user=request.user)
    
    if grant.status.lower() != 'approved':
        messages.error(request, 'Your application has not been approved yet.')
        return redirect('grants:status')
    
    return render(request, 'grants/approval.html', {'application': grant})


@login_required
def ai_insights(request):
    # Show AI-generated summary/score for the current user's application
    grant = GrantApplication.objects.filter(user=request.user).last()
    if not grant:
        return render(request, 'grants/ai_insights.html', {'error': 'No application found.'})

    text = f"Full name: {grant.full_name}. Address: {grant.address}. Amount: {grant.amount_requested}."
    text += f" Application created: {grant.created_at}."

    result = ai_helper.analyze_text(text)
    return render(request, 'grants/ai_insights.html', {'grant': grant, 'ai': result})