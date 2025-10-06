"""
Django signals for Grant Application status changes
Handles automatic notifications and status updates
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import GrantApplication, AuditLog
import logging

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=GrantApplication)
def track_status_changes(sender, instance, **kwargs):
    """Track status changes for audit purposes"""
    if instance.pk:  # Only for existing objects
        try:
            old_instance = GrantApplication.objects.get(pk=instance.pk)
            
            # Check if status changed
            if old_instance.status != instance.status:
                # Create audit log entry
                AuditLog.objects.create(
                    user=getattr(instance, '_updated_by', None),  # Set by admin action
                    action_type='status_changed',
                    object_type='GrantApplication',
                    object_id=str(instance.id),
                    description=f'Status changed from {old_instance.get_status_display()} to {instance.get_status_display()}',
                    additional_data={
                        'old_status': old_instance.status,
                        'new_status': instance.status,
                        'application_id': instance.id,
                        'user_email': instance.email,
                        'amount_requested': instance.amount_requested,
                        'approved_amount': instance.approved_amount
                    }
                )
                
                # Set approval date if status changed to approved and no date is set
                if instance.status == 'approved' and not instance.approval_date:
                    instance.approval_date = timezone.now()
                
                # Set approved amount if approved but no amount set
                if instance.status == 'approved' and not instance.approved_amount:
                    instance.approved_amount = instance.amount_requested
                    
                # Update stage based on status
                if instance.status == 'approved':
                    instance.current_stage = 'completed'
                elif instance.status == 'under_review':
                    instance.current_stage = 'review'
                elif instance.status == 'rejected':
                    instance.current_stage = 'decision'
                    
        except GrantApplication.DoesNotExist:
            pass

@receiver(post_save, sender=GrantApplication)
def send_status_notification(sender, instance, created, **kwargs):
    """Send email notification when status changes"""
    if not created and instance.email:  # Only for existing applications with email
        try:
            # Check if this is a status change (we can determine this from the audit log)
            recent_audit = AuditLog.objects.filter(
                action_type='status_changed',
                object_id=str(instance.id),
                timestamp__gte=timezone.now() - timezone.timedelta(minutes=1)
            ).first()
            
            if recent_audit:
                # Send appropriate notification based on new status
                if instance.status == 'approved':
                    send_approval_notification(instance)
                elif instance.status == 'rejected':
                    send_rejection_notification(instance)
                elif instance.status == 'under_review':
                    send_review_notification(instance)
                elif instance.status == 'on_hold':
                    send_hold_notification(instance)
                    
        except Exception as e:
            logger.error(f"Failed to send status notification for application {instance.id}: {str(e)}")

def send_approval_notification(grant):
    """Send approval notification email"""
    try:
        subject = 'Grant Application Approved - David Johnson Foundation'
        message = f'''Dear {grant.full_name},

🎉 CONGRATULATIONS! Your grant application has been APPROVED! 🎉

Grant Details:
- Application ID: DJF-{grant.id:04d}
- Project Title: {grant.project_title}
- Approved Amount: ${grant.approved_amount:,}
- Approval Date: {grant.approval_date.strftime('%B %d, %Y')}

What's Next:
1. Log in to your account to view your official approval letter
2. Review the next steps for fund disbursement
3. Follow the instructions in your approval letter for receiving funds

Important: Please log in to your account at our website and go to "Check Status" to view your complete approval documentation and fund disbursement instructions.

We're excited to support your impactful project and look forward to seeing the positive change you'll create in your community!

Congratulations again on this achievement!

Best regards,
David Johnson Foundation Team

---
This is an official notification. Please log in to your account for complete documentation.'''

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [grant.email],
            fail_silently=False,
        )
        logger.info(f"Approval notification sent to {grant.email} for application {grant.id}")
        
    except Exception as e:
        logger.error(f"Failed to send approval notification for application {grant.id}: {str(e)}")

def send_rejection_notification(grant):
    """Send rejection notification email"""
    try:
        subject = 'Grant Application Update - David Johnson Foundation'
        message = f'''Dear {grant.full_name},

Thank you for your interest in the David Johnson Foundation grant program.

After careful review by our grant committee, we regret to inform you that your application for "{grant.project_title}" was not selected for funding in this cycle.

This decision does not reflect the value of your project or your commitment to your community. Due to the high volume of applications and limited funding available, we can only approve a small percentage of requests.

We encourage you to:
• Review our grant guidelines for future alignment with our funding priorities
• Consider reapplying in future funding cycles (applications typically open quarterly)
• Explore other funding opportunities that may be a better fit for your project
• Continue pursuing your important work in the community

While we cannot provide individual feedback on applications, our website contains resources and tips for successful grant applications.

Thank you for your dedication to making a positive impact. We wish you success in your future endeavors.

Best regards,
David Johnson Foundation Review Committee

---
For general inquiries, please visit our website or contact our support team.'''

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [grant.email],
            fail_silently=False,
        )
        logger.info(f"Rejection notification sent to {grant.email} for application {grant.id}")
        
    except Exception as e:
        logger.error(f"Failed to send rejection notification for application {grant.id}: {str(e)}")

def send_review_notification(grant):
    """Send under review notification email"""
    try:
        subject = 'Grant Application Under Review - David Johnson Foundation'
        message = f'''Dear {grant.full_name},

We want to update you on the status of your grant application.

Application Details:
- Application ID: DJF-{grant.id:04d}
- Project Title: {grant.project_title}
- Amount Requested: ${grant.amount_requested:,}
- Current Status: Under Review

Your application is now being carefully evaluated by our grant review committee. This process typically takes 2-4 weeks, during which our team will:

• Review your project proposal and budget
• Assess alignment with our funding priorities
• Evaluate the potential impact of your project
• Consider available funding allocation

What You Can Expect:
• You will receive email notification once a decision is made
• No additional action is required from you at this time
• You can check your application status anytime by logging into your account

We appreciate your patience during this important review process. Our committee takes great care in evaluating each application to ensure we support the most impactful projects.

If you have any urgent questions or need to provide additional information, please don't hesitate to contact us.

Thank you for your continued interest in the David Johnson Foundation.

Best regards,
David Johnson Foundation Review Team

---
You can check your application status anytime at our website by logging into your account.'''

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [grant.email],
            fail_silently=False,
        )
        logger.info(f"Review notification sent to {grant.email} for application {grant.id}")
        
    except Exception as e:
        logger.error(f"Failed to send review notification for application {grant.id}: {str(e)}")

def send_hold_notification(grant):
    """Send on hold notification email"""
    try:
        subject = 'Grant Application On Hold - Action May Be Required'
        message = f'''Dear {grant.full_name},

We're writing to update you on the status of your grant application.

Application Details:
- Application ID: DJF-{grant.id:04d}
- Project Title: {grant.project_title}
- Current Status: On Hold

Your application has been placed on hold for the following reason:
{grant.approval_notes if grant.approval_notes else "Additional review or information required"}

What This Means:
• Your application is not rejected - it's temporarily paused
• We may need additional information or clarification
• This could be due to budget considerations or timing
• We will contact you directly if any action is needed from you

Next Steps:
• Please check your email regularly for any requests from our team
• No immediate action is required unless we contact you
• You can check your application status anytime by logging into your account
• Feel free to contact us if you have questions

We appreciate your patience and understanding. Placing an application on hold allows us to give it proper consideration when circumstances are more favorable.

If you have any questions about your application status, please don't hesitate to reach out to our team.

Best regards,
David Johnson Foundation Review Team

---
For questions, please contact our support team through your application portal.'''

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [grant.email],
            fail_silently=False,
        )
        logger.info(f"Hold notification sent to {grant.email} for application {grant.id}")
        
    except Exception as e:
        logger.error(f"Failed to send hold notification for application {grant.id}: {str(e)}")