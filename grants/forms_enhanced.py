from django import forms
from django.contrib.auth.models import User
from .models import (
    GrantApplication, GrantDocument, DocumentType, Message, 
    SuccessStory, ProgressReport, ExpenseReport
)
from django.core.validators import FileExtensionValidator
import json

class MultiStageApplicationForm(forms.ModelForm):
    """Multi-stage application form with progress tracking"""
    
    class Meta:
        model = GrantApplication
        fields = [
            'full_name', 'email', 'phone', 'address',
            'organization_name', 'organization_type', 'tax_id', 'years_established', 'website',
            'project_title', 'project_category', 'project_description', 'project_goals',
            'target_beneficiaries', 'expected_impact', 'amount_requested', 'budget_breakdown',
            'other_funding', 'project_start_date', 'project_duration', 'implementation_plan',
            'experience', 'team_members', 'challenges', 'sustainability', 'additional_info'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 (872) 228-1570'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full mailing address including city, state, and zip code'}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of your organization or project'}),
            'organization_type': forms.Select(attrs={'class': 'form-select'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12-3456789 (optional)'}),
            'years_established': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'e.g., 5'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.yourorganization.org'}),
            'project_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Give your project a compelling title'}),
            'project_category': forms.Select(attrs={'class': 'form-select'}),
            'project_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Describe your project in detail (minimum 200 words)'}),
            'project_goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'What do you hope to achieve?'}),
            'target_beneficiaries': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Who will benefit from this project?'}),
            'expected_impact': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'How will you measure success?'}),
            'amount_requested': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '$10,000', 'min': 1000, 'max': 50000, 'step': 1000}),
            'budget_breakdown': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'How will the funds be used? Provide detailed breakdown.'}),
            'other_funding': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': "List any other grants, donations, or funding sources (current or pending)"}),
            'project_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'mm/dd/yyyy'}),
            'project_duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 6 months, 1 year, 18 months'}),
            'implementation_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'How will you execute this project?'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': "Describe your organization's or your relevant experience"}),
            'team_members': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List key people involved and their roles'}),
            'challenges': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What challenges do you anticipate and how will you address them?'}),
            'sustainability': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'How will the project continue after the grant period?'}),
            'additional_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Anything else you\'d like us to know?'}),
        }

class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents"""
    
    class Meta:
        model = GrantDocument
        fields = ['document_type', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.txt'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Brief description of this document'}),
        }
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            # Check file size (10MB limit)
            if file.size > 10485760:
                raise forms.ValidationError("File size must be under 10MB.")
            
            # Check file extension
            allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt']
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(f"File type .{file_extension} is not allowed. Allowed types: {', '.join(allowed_extensions)}")
        
        return file

class MessageForm(forms.ModelForm):
    """Form for sending messages"""
    
    class Meta:
        model = Message
        fields = ['subject', 'content', 'message_type']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Message subject'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Type your message here...'}),
            'message_type': forms.Select(attrs={'class': 'form-select'}),
        }

class SuccessStoryForm(forms.ModelForm):
    """Form for submitting success stories"""
    
    class Meta:
        model = SuccessStory
        fields = ['title', 'story', 'impact_description', 'video_url', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title of your success story'}),
            'story': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Tell your story...'}),
            'impact_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the impact of the grant'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'YouTube or video link (optional)'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProgressReportForm(forms.ModelForm):
    """Form for submitting progress reports"""
    
    class Meta:
        model = ProgressReport
        fields = [
            'report_period', 'activities_completed', 'challenges_faced',
            'funds_used', 'remaining_funds', 'next_steps'
        ]
        widgets = {
            'report_period': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Month 1, Quarter 2'}),
            'activities_completed': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'What activities have you completed?'}),
            'challenges_faced': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any challenges or obstacles?'}),
            'funds_used': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'remaining_funds': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'next_steps': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What are your next steps?'}),
        }

class ExpenseReportForm(forms.ModelForm):
    """Form for submitting expense reports"""
    
    expense_breakdown_json = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    class Meta:
        model = ExpenseReport
        fields = ['reporting_period', 'total_expenses', 'notes']
        widgets = {
            'reporting_period': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., January 2025, Q1 2025'}),
            'total_expenses': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes or comments'}),
        }
    
    def clean_expense_breakdown_json(self):
        data = self.cleaned_data['expense_breakdown_json']
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Invalid expense breakdown data")
        return {}
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('expense_breakdown_json'):
            instance.expense_breakdown = self.cleaned_data['expense_breakdown_json']
        if commit:
            instance.save()
        return instance

class EligibilityScreeningForm(forms.Form):
    """Initial eligibility screening form"""
    
    is_us_citizen = forms.BooleanField(
        label="Are you a U.S. citizen or legal resident?",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    age_confirmation = forms.BooleanField(
        label="Are you 18 years or older?",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    financial_need = forms.BooleanField(
        label="Do you have a demonstrated financial need?",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    project_readiness = forms.BooleanField(
        label="Do you have a specific project or need for which you're requesting funding?",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    previous_grants = forms.ChoiceField(
        label="Have you received grants from the David Johnson Foundation before?",
        choices=[
            ('no', 'No'),
            ('yes_completed', 'Yes, and I completed all requirements'),
            ('yes_pending', 'Yes, and I have pending obligations'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='no'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check if all eligibility requirements are met
        required_fields = ['is_us_citizen', 'age_confirmation', 'financial_need', 'project_readiness']
        for field in required_fields:
            if not cleaned_data.get(field):
                raise forms.ValidationError(f"You must meet all eligibility requirements to proceed.")
        
        # Check previous grants
        if cleaned_data.get('previous_grants') == 'yes_pending':
            raise forms.ValidationError("You must complete all obligations from previous grants before applying for new funding.")
        
        return cleaned_data

class InterviewSchedulingForm(forms.Form):
    """Form for scheduling interviews"""
    
    preferred_date_1 = forms.DateTimeField(
        label="First Preference",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    
    preferred_date_2 = forms.DateTimeField(
        label="Second Preference",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    
    preferred_date_3 = forms.DateTimeField(
        label="Third Preference",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    
    interview_type = forms.ChoiceField(
        label="Preferred Interview Method",
        choices=[
            ('video', 'Video Call (Zoom/Teams)'),
            ('phone', 'Phone Call'),
            ('in_person', 'In-Person (if local)'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='video'
    )
    
    special_requirements = forms.CharField(
        label="Special Requirements or Accommodations",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any special accommodations needed?'}),
        required=False
    )