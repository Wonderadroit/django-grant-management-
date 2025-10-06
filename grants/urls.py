from django.urls import path
from . import views, views_enhanced, admin_views

app_name = 'grants'

urlpatterns = [
    # Original URLs
    path('dashboard/', views.dashboard, name='dashboard'),  # User dashboard
    path('', views.apply_for_grant, name='apply'),
    path('wait/', views.wait, name='wait'),
    path('status/', views.check_status, name='status'),
    path('approval/', views.approval_letter, name='approval'),
    path('ai-insights/', views.ai_insights, name='ai_insights'),
    
    # Admin Dashboard
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/api/', admin_views.dashboard_api, name='dashboard_api'),
    
    # Multi-Stage Application Process
    path('eligibility/', views_enhanced.eligibility_screening, name='eligibility'),
    path('application-details/', views_enhanced.application_details, name='application_details'),
    path('document-upload/', views_enhanced.document_upload, name='document_upload'),
    path('application-review/', views_enhanced.application_review, name='application_review'),
    path('interview-scheduling/', views_enhanced.interview_scheduling, name='interview_scheduling'),
    
    # Document management
    path('upload-document/', views_enhanced.upload_document, name='upload_document'),
    path('get-document-status/', views_enhanced.get_document_status, name='get_document_status'),
    path('update-application-stage/', views_enhanced.update_application_stage, name='update_application_stage'),
    
    # Grant Recipient Portal
    path('recipient-portal/', views_enhanced.recipient_portal, name='recipient_portal'),
    path('submit-progress-report/', views_enhanced.submit_progress_report, name='submit_progress_report'),
    path('submit-expense-report/', views_enhanced.submit_expense_report, name='submit_expense_report'),
    
    # Communication
    path('messages/', views_enhanced.messages_view, name='messages'),
    path('send-message/', views_enhanced.send_message, name='send_message'),
    path('get-message/', views_enhanced.get_message, name='get_message'),
    path('delete-message/', views_enhanced.delete_message, name='delete_message'),
    path('mark-messages-read/', views_enhanced.mark_messages_read, name='mark_messages_read'),
    path('get-unread-count/', views_enhanced.get_unread_count, name='get_unread_count'),
    
    # Community Features
    path('success-stories/', views_enhanced.success_stories_list, name='success_stories'),
    path('success-story/submit/', views_enhanced.submit_success_story, name='submit_success_story'),
    path('success-story/<int:story_id>/', views_enhanced.view_success_story, name='view_success_story'),
    path('community/', views_enhanced.community_dashboard, name='community_dashboard'),
    
    # Financial Management
    path('financial/', views_enhanced.financial_dashboard, name='financial_dashboard'),
    path('process-disbursement/<int:application_id>/', views_enhanced.process_disbursement, name='process_disbursement'),
    
    # Security & Compliance
    path('security/', views_enhanced.security_dashboard, name='security_dashboard'),
    path('audit-log/', views_enhanced.audit_log_view, name='audit_log_view'),
    path('compliance-report/', views_enhanced.compliance_report, name='compliance_report'),
    
    # Analytics
    path('analytics/', views_enhanced.analytics_dashboard, name='analytics_dashboard'),
    path('export-analytics/', views_enhanced.export_analytics, name='export_analytics'),
    
    # AJAX Endpoints
    path('get-application-progress/', views_enhanced.get_application_progress, name='get_application_progress'),
]