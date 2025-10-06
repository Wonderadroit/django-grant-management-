from django.db import models
from django.contrib.auth.models import User
import os
from django.core.validators import FileExtensionValidator
from django.utils import timezone

def get_upload_path(instance, filename):
    """Generate upload path for documents"""
    return f'grant_documents/{instance.application.user.id}/{instance.document_type}/{filename}'

class DocumentType(models.Model):
    """Types of documents that can be uploaded"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    required = models.BooleanField(default=False)
    max_file_size = models.IntegerField(default=10485760)  # 10MB default
    allowed_extensions = models.CharField(max_length=200, default='pdf,doc,docx,jpg,jpeg,png')
    display_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name

class GrantDocument(models.Model):
    """Documents uploaded for grant applications"""
    application = models.ForeignKey('GrantApplication', on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt'])]
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.application.full_name} - {self.document_type.name}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = self.file.name
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-uploaded_at']

class GrantApplication(models.Model):
    ORGANIZATION_TYPES = [
        ('nonprofit', 'Non-Profit Organization'),
        ('community', 'Community Group'),
        ('religious', 'Religious Organization'),
        ('educational', 'Educational Institution'),
        ('healthcare', 'Healthcare Organization'),
        ('other', 'Other Organization'),
    ]
    
    PROJECT_CATEGORIES = [
        ('essential_needs', 'Essential Needs (Food, Utilities, etc.)'),
        ('healthcare', 'Healthcare & Medical'),
        ('education', 'Education & Training'),
        ('housing', 'Housing & Rent Assistance'),
        ('emergency', 'Emergency Financial Aid'),
        ('debt_relief', 'Debt Relief'),
        ('disability', 'Disability Support'),
        ('senior_care', 'Senior Care'),
        ('childcare', 'Childcare Support'),
        ('other', 'Other'),
    ]
    
    APPLICATION_STAGES = [
        ('draft', 'Draft'),
        ('eligibility', 'Eligibility Screening'),
        ('details', 'Detailed Application'),
        ('documents', 'Document Upload'),
        ('review', 'Under Review'),
        ('interview', 'Interview/Clarification'),
        ('decision', 'Final Decision'),
        ('completed', 'Completed'),
    ]

    # Basic Information
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)  # Allow anonymous applications
    full_name = models.CharField(max_length=200, verbose_name="Full Name")
    email = models.EmailField(verbose_name="Email Address")
    phone = models.CharField(max_length=20, verbose_name="Phone Number", default="")
    address = models.TextField(verbose_name="Full Address")
    
    # Organization Details (Optional - for organizational applications)
    organization_name = models.CharField(max_length=300, verbose_name="Organization/Project Name", blank=True, default="")
    organization_type = models.CharField(max_length=20, choices=ORGANIZATION_TYPES, verbose_name="Organization Type", blank=True, default="nonprofit")
    tax_id = models.CharField(max_length=50, blank=True, verbose_name="Tax ID/EIN (if applicable)", help_text="For tax-exempt organizations")
    years_established = models.IntegerField(blank=True, null=True, verbose_name="Years Established", help_text="e.g., 5")
    website = models.URLField(blank=True, verbose_name="Website (if any)", help_text="https://www.yourorganization.org")
    
    # Project Information
    project_title = models.CharField(max_length=300, verbose_name="Project Title", default="")
    project_category = models.CharField(max_length=20, choices=PROJECT_CATEGORIES, verbose_name="Project Category", default="community")
    project_description = models.TextField(verbose_name="Detailed Project Description", help_text="Describe your project in detail (minimum 200 words)", default="")
    project_goals = models.TextField(verbose_name="Project Goals & Objectives", help_text="What do you hope to achieve?", default="")
    target_beneficiaries = models.TextField(verbose_name="Target Beneficiaries", help_text="Who will benefit from this project?", default="")
    expected_impact = models.TextField(verbose_name="Expected Impact", help_text="How will you measure success?", default="")
    
    # Financial Information
    amount_requested = models.IntegerField(verbose_name="Grant Amount Requested", default=10000, help_text="Enter amount in dollars")
    budget_breakdown = models.TextField(verbose_name="Budget Breakdown", help_text="Provide a detailed breakdown:\n• Personnel: $X,XXX\n• Equipment: $X,XXX\n• Materials: $X,XXX\n• Other: $X,XXX", default="")
    other_funding = models.TextField(blank=True, verbose_name="Other Funding Sources", help_text="List any other grants, donations, or funding sources (current or pending)")
    
    # Timeline & Implementation
    project_start_date = models.DateField(verbose_name="Proposed Start Date", null=True, blank=True, help_text="mm/dd/yyyy")
    project_duration = models.CharField(max_length=100, verbose_name="Project Duration", help_text="e.g., 6 months, 1 year, 18 months", default="")
    implementation_plan = models.TextField(verbose_name="Implementation Plan", help_text="Describe your step-by-step plan to implement this project. Include timeline and milestones.", default="")
    
    # Experience & Qualifications
    experience = models.TextField(verbose_name="Relevant Experience", help_text="Describe your organization's relevant experience and qualifications for this project", default="")
    team_members = models.TextField(blank=True, verbose_name="Key Team Members", help_text="List key team members and their roles/qualifications (optional)")
    
    # Additional Information (Optional)
    challenges = models.TextField(blank=True, verbose_name="Potential Challenges", help_text="What challenges do you anticipate and how will you address them? (optional)")
    sustainability = models.TextField(blank=True, verbose_name="Sustainability Plan", help_text="How will the project continue or have lasting impact after the grant period? (optional)")
    additional_info = models.TextField(blank=True, verbose_name="Additional Information", help_text="Any additional information you'd like to share (optional)")
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('on_hold', 'On Hold'),
    ]
    
    # System fields
    current_stage = models.CharField(max_length=20, choices=APPLICATION_STAGES, default='draft')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    approval_date = models.DateTimeField(null=True, blank=True, verbose_name="Date Approved")
    approval_notes = models.TextField(blank=True, verbose_name="Approval/Rejection Notes")
    approved_amount = models.IntegerField(null=True, blank=True, verbose_name="Approved Amount")
    
    # Document tracking
    documents_complete = models.BooleanField(default=False)
    documents_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    
    # Interview tracking
    interview_scheduled = models.BooleanField(default=False)
    interview_date = models.DateTimeField(null=True, blank=True)
    interview_notes = models.TextField(blank=True)
    interview_completed = models.BooleanField(default=False)
    
    # Progress tracking
    progress_percentage = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        name = self.organization_name if self.organization_name else f"{self.full_name} (Individual)"
        return f"{name} - ${self.amount_requested:,} ({self.status})"
    
    def get_progress_percentage(self):
        """Calculate application progress based on current stage"""
        stage_progress = {
            'draft': 10,
            'eligibility': 25,
            'details': 50,
            'documents': 75,
            'review': 85,
            'interview': 95,
            'decision': 100,
            'completed': 100,
        }
        return stage_progress.get(self.current_stage, 0)
    
    def get_required_documents(self):
        """Get list of required documents for this application"""
        return DocumentType.objects.filter(required=True)
    
    def get_missing_documents(self):
        """Get list of missing required documents"""
        uploaded_types = self.documents.values_list('document_type', flat=True)
        return DocumentType.objects.filter(required=True).exclude(id__in=uploaded_types)
    
    class Meta:
        verbose_name = "Grant Application"
        verbose_name_plural = "Grant Applications"
        ordering = ['-created_at']

# Community and Communication Models
class Message(models.Model):
    """Messages between applicants and reviewers"""
    MESSAGE_TYPES = [
        ('general', 'General'),
        ('clarification', 'Clarification Request'),
        ('document', 'Document Related'),
        ('interview', 'Interview Related'),
        ('update', 'Status Update'),
    ]
    
    application = models.ForeignKey(GrantApplication, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='general')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    is_internal = models.BooleanField(default=False)  # Internal staff notes
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} - {self.subject}"

def success_story_image_path(instance, filename):
    """Generate upload path for success story images"""
    import os
    from django.utils.text import slugify
    
    # Get file extension
    ext = filename.split('.')[-1]
    # Create new filename: success_story_id_timestamp.ext
    new_filename = f"success_story_{instance.success_story.id if instance.success_story.id else 'new'}_{int(timezone.now().timestamp())}.{ext}"
    return os.path.join('success_stories/', new_filename)

class SuccessStory(models.Model):
    """Success stories from grant recipients"""
    application = models.OneToOneField(GrantApplication, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    story = models.TextField()
    impact_description = models.TextField()
    metrics = models.JSONField(default=dict, blank=True)  # Store impact metrics
    video_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    def get_images(self):
        """Get all images associated with this success story"""
        return self.images.all()
    
    def get_featured_image(self):
        """Get the first/main image for this success story"""
        return self.images.first()

class SuccessStoryImage(models.Model):
    """Images attached to success stories/testimonials"""
    success_story = models.ForeignKey(SuccessStory, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=success_story_image_path)
    caption = models.CharField(max_length=500, blank=True)
    alt_text = models.CharField(max_length=200, blank=True, help_text="Alternative text for accessibility")
    is_primary = models.BooleanField(default=False, help_text="Main image for this testimonial")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'uploaded_at']
    
    def __str__(self):
        return f"Image for {self.success_story.title}"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, make sure no other image is primary
        if self.is_primary:
            SuccessStoryImage.objects.filter(
                success_story=self.success_story, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

class ProgressReport(models.Model):
    """Progress reports from grant recipients"""
    application = models.ForeignKey(GrantApplication, on_delete=models.CASCADE, related_name='progress_reports')
    report_period = models.CharField(max_length=50)  # e.g., "Month 1", "Quarter 2"
    activities_completed = models.TextField()
    challenges_faced = models.TextField(blank=True)
    funds_used = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_funds = models.DecimalField(max_digits=10, decimal_places=2)
    next_steps = models.TextField()
    attachments = models.TextField(blank=True)  # File paths
    submitted_date = models.DateTimeField(auto_now_add=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(blank=True)
    approved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.application.organization_name} - {self.report_period}"

# Financial Management Models
class FundDisbursement(models.Model):
    """Track fund disbursements to grant recipients"""
    DISBURSEMENT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('digital_wallet', 'Digital Wallet'),
        ('other', 'Other'),
    ]
    
    application = models.ForeignKey(GrantApplication, on_delete=models.CASCADE, related_name='disbursements')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    disbursement_method = models.CharField(max_length=20, choices=DISBURSEMENT_METHODS)
    reference_number = models.CharField(max_length=100, unique=True)
    disbursed_date = models.DateTimeField()
    bank_details = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.application.organization_name} - ${self.amount}"

class ExpenseReport(models.Model):
    """Expense reports submitted by grant recipients"""
    application = models.ForeignKey(GrantApplication, on_delete=models.CASCADE, related_name='expense_reports')
    reporting_period = models.CharField(max_length=50)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2)
    expense_breakdown = models.JSONField(default=dict)  # Category-wise breakdown
    receipts_uploaded = models.BooleanField(default=False)
    submitted_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.application.organization_name} - {self.reporting_period}"

# Analytics and Tracking Models
class GrantAnalytics(models.Model):
    """Analytics data for grant applications"""
    date = models.DateField()
    total_applications = models.IntegerField(default=0)
    approved_applications = models.IntegerField(default=0)
    rejected_applications = models.IntegerField(default=0)
    pending_applications = models.IntegerField(default=0)
    total_amount_requested = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount_approved = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_processing_time = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # days
    category_breakdown = models.JSONField(default=dict)
    geographic_distribution = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.date}"

class AuditLog(models.Model):
    """Audit trail for all important actions"""
    ACTION_TYPES = [
        ('application_created', 'Application Created'),
        ('application_updated', 'Application Updated'),
        ('status_changed', 'Status Changed'),
        ('document_uploaded', 'Document Uploaded'),
        ('document_verified', 'Document Verified'),
        ('funds_disbursed', 'Funds Disbursed'),
        ('report_submitted', 'Report Submitted'),
        ('user_login', 'User Login'),
        ('admin_action', 'Admin Action'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    object_type = models.CharField(max_length=50)  # e.g., 'GrantApplication', 'Document'
    object_id = models.CharField(max_length=50)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.timestamp}"


class GrantSettings(models.Model):
    """System-wide grant application settings"""
    approval_deadline_hours = models.IntegerField(default=24, help_text="Hours for approval decision")
    processing_time_weeks_min = models.IntegerField(default=2, help_text="Minimum processing time in weeks")
    processing_time_weeks_max = models.IntegerField(default=4, help_text="Maximum processing time in weeks")
    review_frequency = models.CharField(max_length=50, default="Monthly", help_text="How often applications are reviewed")
    welcome_message = models.TextField(
        default="Welcome to the Dave Johnson Foundation Grant Application. Please complete all sections carefully. Our review process typically takes 2-4 weeks. Applications are reviewed monthly by our grant committee.",
        help_text="Message shown to applicants"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Grant Settings"
        verbose_name_plural = "Grant Settings"
    
    def __str__(self):
        return f"Grant Settings - Approval: {self.approval_deadline_hours}h, Processing: {self.processing_time_weeks_min}-{self.processing_time_weeks_max}w"