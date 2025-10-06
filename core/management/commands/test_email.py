from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from grants.models import GrantApplication
from core.email_service import EmailService
import sys

class Command(BaseCommand):
    help = 'Test email functionality with sample emails'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test emails to',
            required=True
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['welcome', 'approval', 'rejection', 'status', 'all'],
            default='welcome',
            help='Type of email to test'
        )
    
    def handle(self, *args, **options):
        test_email = options['email']
        email_type = options['type']
        
        self.stdout.write(f"Testing email functionality...")
        self.stdout.write(f"Target email: {test_email}")
        self.stdout.write(f"Email type: {email_type}")
        self.stdout.write("-" * 50)
        
        # Create or get test user
        test_user, created = User.objects.get_or_create(
            email=test_email,
            defaults={
                'username': f'test_user_{test_email.split("@")[0]}',
                'first_name': 'Test',
                'last_name': 'User',
            }
        )
        
        if created:
            self.stdout.write(f"Created test user: {test_user.username}")
        
        # Create or get test application
        test_application, created = GrantApplication.objects.get_or_create(
            user=test_user,
            defaults={
                'full_name': 'Test User Application',
                'email': test_email,
                'phone': '+1 (872) 228-1570',
                'address': '123 Test Street, Test City, TS 12345',
                'organization_name': 'Test Community Organization',
                'organization_type': 'nonprofit',
                'project_title': 'Community Development Test Project',
                'project_category': 'community',
                'project_description': 'This is a test grant application for email functionality testing.',
                'project_goals': 'To test the email system and ensure proper delivery.',
                'target_beneficiaries': 'Community members and email testing volunteers.',
                'expected_impact': 'Successful email delivery and professional presentation.',
                'amount_requested': 25000,
                'budget_breakdown': 'Personnel: $15,000\nEquipment: $5,000\nOperating Costs: $5,000',
                'project_duration': '12 months',
                'implementation_plan': 'Test and verify email delivery systems.',
                'experience': 'Extensive experience in email testing and grant management.',
                'status': 'pending',
                'approved_amount': 25000,
                'approval_notes': 'Excellent project with clear objectives and measurable outcomes. The committee is impressed with the comprehensive approach and community impact potential.',
            }
        )
        
        if created:
            self.stdout.write(f"Created test application for {test_application.full_name}")
        
        # Send emails based on type
        success_count = 0
        total_count = 0
        
        if email_type == 'welcome' or email_type == 'all':
            self.stdout.write("Sending welcome email...")
            if EmailService.send_welcome_email(test_user):
                self.stdout.write(self.style.SUCCESS("✓ Welcome email sent successfully"))
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR("✗ Welcome email failed"))
            total_count += 1
        
        if email_type == 'approval' or email_type == 'all':
            self.stdout.write("Sending approval email...")
            test_application.status = 'approved'
            test_application.save()
            if EmailService.send_approval_email(test_application):
                self.stdout.write(self.style.SUCCESS("✓ Approval email sent successfully"))
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR("✗ Approval email failed"))
            total_count += 1
        
        if email_type == 'rejection' or email_type == 'all':
            self.stdout.write("Sending rejection email...")
            test_application.status = 'rejected'
            test_application.approval_notes = 'While your project shows merit, we received many excellent applications and have limited funding available this cycle. We encourage you to refine your proposal and apply again in our next funding round.'
            test_application.save()
            if EmailService.send_rejection_email(test_application):
                self.stdout.write(self.style.SUCCESS("✓ Rejection email sent successfully"))
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR("✗ Rejection email failed"))
            total_count += 1
        
        if email_type == 'status' or email_type == 'all':
            self.stdout.write("Sending status update email...")
            test_application.status = 'under_review'
            test_application.save()
            if EmailService.send_status_update_email(test_application):
                self.stdout.write(self.style.SUCCESS("✓ Status update email sent successfully"))
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR("✗ Status update email failed"))
            total_count += 1
        
        # Summary
        self.stdout.write("-" * 50)
        self.stdout.write(f"Email test completed: {success_count}/{total_count} emails sent successfully")
        
        if success_count == total_count:
            self.stdout.write(self.style.SUCCESS("🎉 All emails sent successfully!"))
        elif success_count > 0:
            self.stdout.write(self.style.WARNING(f"⚠️  {total_count - success_count} emails failed"))
        else:
            self.stdout.write(self.style.ERROR("❌ All email sends failed"))
            
        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Check your email inbox for the test emails")
        self.stdout.write("2. If using console backend, check the server terminal output")
        self.stdout.write("3. For Gmail SMTP, ensure you've set up an App Password")
        self.stdout.write("4. For production, consider switching to SendGrid or similar service")