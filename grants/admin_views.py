from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from .models import GrantApplication, GrantSettings, AuditLog
from django.contrib.auth.models import User

@staff_member_required
def admin_dashboard(request):
    """Custom admin dashboard with statistics and charts"""
    
    # Calculate date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Basic statistics
    total_applications = GrantApplication.objects.count()
    pending_applications = GrantApplication.objects.filter(status='pending').count()
    approved_applications = GrantApplication.objects.filter(status='approved').count()
    total_approved_amount = GrantApplication.objects.filter(status='approved').aggregate(
        total=Sum('approved_amount')
    )['total'] or 0
    
    # Recent statistics
    applications_this_week = GrantApplication.objects.filter(created_at__gte=week_ago).count()
    applications_this_month = GrantApplication.objects.filter(created_at__gte=month_ago).count()
    
    # Approval rate
    if total_applications > 0:
        approval_rate = (approved_applications / total_applications) * 100
    else:
        approval_rate = 0
    
    # Average processing time
    approved_apps_with_dates = GrantApplication.objects.filter(
        status='approved', 
        approval_date__isnull=False
    )
    
    avg_processing_days = 0
    if approved_apps_with_dates.exists():
        total_days = sum([
            (app.approval_date.date() - app.created_at.date()).days 
            for app in approved_apps_with_dates
        ])
        avg_processing_days = total_days / approved_apps_with_dates.count()
    
    # Applications by status
    status_data = GrantApplication.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Applications by category
    category_data = GrantApplication.objects.values('project_category').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Recent applications (last 10)
    recent_applications = GrantApplication.objects.select_related('user').order_by('-created_at')[:10]
    
    # Applications needing attention (pending > 24 hours)
    attention_needed = GrantApplication.objects.filter(
        status='pending',
        created_at__lte=timezone.now() - timedelta(hours=24)
    ).count()
    
    # Monthly trend data for charts
    monthly_data = []
    for i in range(6):
        month_start = today.replace(day=1) - timedelta(days=i*30)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_apps = GrantApplication.objects.filter(
            created_at__date__gte=month_start,
            created_at__date__lte=month_end
        ).count()
        
        month_approved = GrantApplication.objects.filter(
            approval_date__date__gte=month_start,
            approval_date__date__lte=month_end
        ).count()
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'applications': month_apps,
            'approved': month_approved
        })
    
    monthly_data.reverse()  # Show oldest to newest
    
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    users_with_applications = User.objects.filter(grantapplication__isnull=False).count()
    
    context = {
        'title': 'Grant Management Dashboard',
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'total_approved_amount': total_approved_amount,
        'applications_this_week': applications_this_week,
        'applications_this_month': applications_this_month,
        'approval_rate': round(approval_rate, 1),
        'avg_processing_days': round(avg_processing_days, 1),
        'status_data': list(status_data),
        'category_data': list(category_data),
        'recent_applications': recent_applications,
        'attention_needed': attention_needed,
        'monthly_data': monthly_data,
        'total_users': total_users,
        'active_users': active_users,
        'users_with_applications': users_with_applications,
    }
    
    return render(request, 'admin/grants/dashboard.html', context)

@staff_member_required
def dashboard_api(request):
    """API endpoint for dashboard charts"""
    chart_type = request.GET.get('type', 'status')
    
    if chart_type == 'status':
        data = list(GrantApplication.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status'))
        return JsonResponse({'data': data})
    
    elif chart_type == 'category':
        data = list(GrantApplication.objects.values('project_category').annotate(
            count=Count('id')
        ).order_by('-count')[:10])
        return JsonResponse({'data': data})
    
    elif chart_type == 'monthly':
        # Get last 12 months of data
        monthly_data = []
        today = timezone.now().date()
        
        for i in range(12):
            month_start = (today.replace(day=1) - timedelta(days=i*30))
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            applications = GrantApplication.objects.filter(
                created_at__date__gte=month_start,
                created_at__date__lte=month_end
            ).count()
            
            approved = GrantApplication.objects.filter(
                status='approved',
                approval_date__date__gte=month_start,
                approval_date__date__lte=month_end
            ).count()
            
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'applications': applications,
                'approved': approved
            })
        
        monthly_data.reverse()
        return JsonResponse({'data': monthly_data})
    
    return JsonResponse({'error': 'Invalid chart type'})