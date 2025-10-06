# Email Service Module for Dave Johnson Foundation Grant System
# This module provides email sending functionality with professional HTML templates

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """
    Centralized email service for the grant management system
    """
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new users"""
        try:
            subject = 'Welcome to Dave Johnson Foundation - Grant Platform'
            
            # Render HTML email
            html_message = render_to_string('email/welcome_email.html', {
                'user': user,
            })
            
            # Create plain text version
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Welcome email sent successfully to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_approval_email(application):
        """Send approval congratulations email"""
        try:
            subject = f'🎉 Grant Approved - ${application.approved_amount or application.amount_requested:,} Funding Confirmed!'
            
            # Set approval date if not set
            if not application.approval_date:
                application.approval_date = timezone.now()
                application.save()
            
            # Render HTML email
            html_message = render_to_string('email/approval_email.html', {
                'application': application,
            })
            
            # Create plain text version
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Approval email sent successfully to {application.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send approval email to {application.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_rejection_email(application):
        """Send rejection email with encouragement"""
        try:
            subject = 'Grant Application Decision - Dave Johnson Foundation'
            
            # Render HTML email
            html_message = render_to_string('email/rejection_email.html', {
                'application': application,
            })
            
            # Create plain text version
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Rejection email sent successfully to {application.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send rejection email to {application.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_status_update_email(application):
        """Send status update email"""
        try:
            status_messages = {
                'pending': 'Application Received - Under Initial Review',
                'under_review': 'Application Under Committee Review',
                'on_hold': 'Application On Hold - Action Required',
                'approved': 'Application Approved!',
                'rejected': 'Application Decision'
            }
            
            subject = f"Grant Application Update: {status_messages.get(application.status, 'Status Update')}"
            
            # Render HTML email
            html_message = render_to_string('email/status_update_email.html', {
                'application': application,
            })
            
            # Create plain text version
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Status update email sent successfully to {application.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send status update email to {application.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_document_request_email(application, missing_documents):
        """Send email requesting missing documents"""
        try:
            subject = 'Missing Documents - Action Required for Your Grant Application'
            
            # Create document list
            doc_list = ', '.join([doc.name for doc in missing_documents])
            
            # Simple email for now (can be enhanced with HTML template later)
            message = f"""
Dear {application.full_name},

Your grant application is currently on hold pending the following missing documents:

{doc_list}

Please log in to your dashboard to upload these documents:
http://127.0.0.1:8000/grants/dashboard/

Once all documents are uploaded, your application will continue through the review process.

If you have any questions, please contact our support team.

Best regards,
David Johnson Foundation Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                fail_silently=False,
            )
            
            logger.info(f"Document request email sent successfully to {application.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send document request email to {application.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_reminder_email(application, reminder_type='general'):
        """Send reminder emails for various purposes"""
        try:
            if reminder_type == 'incomplete_application':
                subject = 'Complete Your Grant Application - Dave Johnson Foundation'
                message = f"""
Dear {application.full_name},

You have an incomplete grant application in our system. Don't miss out on funding opportunities!

Please log in to complete your application:
http://127.0.0.1:8000/grants/dashboard/

Application deadline information and requirements are available in your dashboard.

Best regards,
Dave Johnson Foundation Team
                """
            elif reminder_type == 'progress_report':
                subject = 'Progress Report Due - Grant Recipient Update Required'
                message = f"""
Dear {application.full_name},

This is a friendly reminder that your quarterly progress report is due for your approved grant project.

Please submit your progress report through your recipient portal:
http://127.0.0.1:8000/grants/recipient-portal/

Thank you for keeping us updated on your project's progress.

Best regards,
Dave Johnson Foundation Team
                """
            else:
                subject = 'Reminder - Dave Johnson Foundation'
                message = f"""
Dear {application.full_name},

This is a reminder regarding your grant application with the Dave Johnson Foundation.

Please log in to your dashboard for more information:
http://127.0.0.1:8000/grants/dashboard/

Best regards,
Dave Johnson Foundation Team
                """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                fail_silently=False,
            )
            
            logger.info(f"Reminder email ({reminder_type}) sent successfully to {application.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reminder email to {application.email}: {str(e)}")
            return False

# Convenience functions for easy import
def send_welcome_email(user):
    return EmailService.send_welcome_email(user)

def send_approval_email(application):
    return EmailService.send_approval_email(application)

def send_rejection_email(application):
    return EmailService.send_rejection_email(application)

def send_status_update_email(application):
    return EmailService.send_status_update_email(application)

def send_document_request_email(application, missing_documents):
    return EmailService.send_document_request_email(application, missing_documents)

def send_reminder_email(application, reminder_type='general'):
    return EmailService.send_reminder_email(application, reminder_type)