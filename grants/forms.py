from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import GrantApplication, SuccessStory, SuccessStoryImage

class GrantApplicationForm(forms.ModelForm):
    # honeypot field: should be left blank by real users
    hp = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = GrantApplication
        fields = [
            "full_name", "email", "phone", "address",
            "organization_name", "organization_type", "tax_id", "years_established", "website",
            "project_title", "project_category", "project_description", "project_goals",
            "target_beneficiaries", "expected_impact",
            "amount_requested", "budget_breakdown", "other_funding",
            "project_start_date", "project_duration", "implementation_plan",
            "experience", "team_members",
            "challenges", "sustainability", "additional_info"
        ]
        
        widgets = {
            # Personal Information
            "full_name": forms.TextInput(attrs={
                "class": "form-control", 
                "placeholder": "Enter your full name"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control", 
                "placeholder": "your.email@example.com"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "+1 (872) 228-1570"
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 3, 
                "placeholder": "Full mailing address including city, state, and zip code"
            }),
            
            # Organization Details
            "organization_name": forms.TextInput(attrs={
                "class": "form-control", 
                "placeholder": "Name of your organization or project"
            }),
            "organization_type": forms.Select(attrs={"class": "form-select"}),
            "tax_id": forms.TextInput(attrs={
                "class": "form-control", 
                "placeholder": "12-3456789 (optional)"
            }),
            "years_established": forms.NumberInput(attrs={
                "class": "form-control", 
                "min": "0", 
                "max": "100",
                "placeholder": "e.g., 5"
            }),
            "website": forms.URLInput(attrs={
                "class": "form-control", 
                "placeholder": "https://www.yourorganization.org"
            }),
            
            # Project Information
            "project_title": forms.TextInput(attrs={
                "class": "form-control", 
                "placeholder": "Give your project a compelling title"
            }),
            "project_category": forms.Select(attrs={"class": "form-select"}),
            "project_description": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 6, 
                "placeholder": "Provide a detailed description of your project. What problem does it solve? How will it work? (Minimum 200 words)"
            }),
            "project_goals": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 4, 
                "placeholder": "What specific goals and objectives do you hope to achieve?"
            }),
            "target_beneficiaries": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 3, 
                "placeholder": "Who will benefit from this project? How many people will be impacted?"
            }),
            "expected_impact": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 4, 
                "placeholder": "How will you measure the success of your project? What metrics will you use?"
            }),
            
            # Financial Information
            "amount_requested": forms.Select(attrs={"class": "form-select"}),
            "budget_breakdown": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 5, 
                "placeholder": "Provide a detailed breakdown:\n• Personnel: $X,XXX\n• Equipment: $X,XXX\n• Materials: $X,XXX\n• Other: $X,XXX"
            }),
            "other_funding": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 3, 
                "placeholder": "List any other grants, donations, or funding sources (current or pending)"
            }),
            
            # Timeline & Implementation
            "project_start_date": forms.DateInput(attrs={
                "class": "form-control", 
                "type": "date"
            }),
            "project_duration": forms.TextInput(attrs={
                "class": "form-control", 
                "placeholder": "e.g., 6 months, 1 year, 18 months"
            }),
            "implementation_plan": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 5, 
                "placeholder": "Describe your step-by-step plan to implement this project. Include timeline and milestones."
            }),
            
            # Experience & Qualifications
            "experience": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 4, 
                "placeholder": "Describe your organization's relevant experience and qualifications for this project"
            }),
            "team_members": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 4, 
                "placeholder": "List key team members and their roles/qualifications (optional)"
            }),
            
            # Additional Information
            "challenges": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 3, 
                "placeholder": "What challenges do you anticipate and how will you address them? (optional)"
            }),
            "sustainability": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 3, 
                "placeholder": "How will the project continue or have lasting impact after the grant period? (optional)"
            }),
            "additional_info": forms.Textarea(attrs={
                "class": "form-control", 
                "rows": 3, 
                "placeholder": "Any additional information you'd like to share (optional)"
            }),
        }

    def clean_project_description(self):
        description = self.cleaned_data.get('project_description')
        if description and len(description.split()) < 50:  # roughly 200 words minimum
            raise ValidationError("Project description must be at least 50 words. Please provide more detail.")
        return description

    def clean_project_start_date(self):
        start_date = self.cleaned_data.get('project_start_date')
        if start_date and start_date < date.today():
            raise ValidationError("Project start date cannot be in the past.")
        if start_date and start_date > date.today() + timedelta(days=365):
            raise ValidationError("Project start date must be within the next year.")
        return start_date

    def clean_budget_breakdown(self):
        budget = self.cleaned_data.get('budget_breakdown')
        if budget and len(budget.strip()) < 50:
            raise ValidationError("Please provide a detailed budget breakdown with specific amounts.")
        return budget

    def clean_experience(self):
        experience = self.cleaned_data.get('experience')
        if experience and len(experience.strip()) < 30:
            raise ValidationError("Please provide more detail about your relevant experience.")
        return experience

    def clean_hp(self):
        # honeypot validation
        hp = self.cleaned_data.get('hp')
        if hp:
            raise ValidationError("Invalid form submission.")
        return hp

class SuccessStoryForm(forms.ModelForm):
    """Form for creating/editing success stories with testimonials"""
    
    class Meta:
        model = SuccessStory
        fields = ['title', 'story', 'impact_description', 'video_url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a compelling title for your success story'
            }),
            'story': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Tell us about your journey and how the grant helped you...'
            }),
            'impact_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the impact your project had on your community...'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional: Add a YouTube or Vimeo video URL'
            })
        }
    
    def clean_story(self):
        story = self.cleaned_data.get('story')
        if story and len(story.strip()) < 100:
            raise ValidationError("Please provide a more detailed story (at least 100 characters).")
        return story

class SuccessStoryImageForm(forms.ModelForm):
    """Form for uploading testimonial images"""
    
    class Meta:
        model = SuccessStoryImage
        fields = ['image', 'caption', 'alt_text', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Describe this image (optional)'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Alternative text for accessibility'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Image file too large. Please keep images under 5MB.")
            
            # Check file type
            if not image.content_type.startswith('image/'):
                raise ValidationError("Please upload a valid image file.")
                
        return image

# Formset for multiple image uploads
SuccessStoryImageFormSet = forms.inlineformset_factory(
    SuccessStory,
    SuccessStoryImage,
    form=SuccessStoryImageForm,
    extra=3,  # Allow 3 images by default
    max_num=10,  # Maximum 10 images per testimonial
    can_delete=True
)