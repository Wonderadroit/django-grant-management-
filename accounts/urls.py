from django.urls import path
from django.contrib.auth import views as auth_views
from authentication.views import login_view, register_user

urlpatterns = [
    path('signup/', register_user, name='signup'),
    path('register/', register_user, name='register'),  # Alias for compatibility
    path('login/', login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # Password change URLs
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/password_change/done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
]
