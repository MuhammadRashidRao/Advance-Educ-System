from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('login/', views.AdvancedLoginView.as_view(), name='login'),
    path('register/', views.AdvancedRegisterView.as_view(), name='register'),
    path('logout/', views.AdvancedLogoutView.as_view(), name='logout'),
    
    # Password reset
    path('password-reset/', views.AdvancedPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.AdvancedPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.AdvancedPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', views.AdvancedPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Dashboard and profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.AdvancedUserProfileView.as_view(), name='profile'),
    path('profile/edit/', views.AdvancedUserUpdateView.as_view(), name='profile_edit'),
    
    # Teacher-specific routes
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/live-session/', views.teacher_live_session, name='teacher_live_session'),
    path('teacher/session-management/', views.teacher_session_management, name='teacher_session_management'),
    
    # Security and settings
    path('security/', views.security_settings, name='security_settings'),
    path('notifications/', views.notification_preferences, name='notification_preferences'),
    path('activity/', views.user_activity, name='user_activity'),
    path('sessions/', views.session_management, name='session_management'),
    
    # Email verification
    path('verify-email/', views.email_verification, name='email_verification'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('verify-2fa/', views.verify_2fa, name='verify_2fa'),
    
    # Admin only (for staff users)
    path('admin/users/', views.user_management, name='user_management'),
    path('admin/users/<int:pk>/', views.user_detail, name='user_detail'),
    
    # API endpoints
    path('api/update-notifications/', views.update_notification_preferences, name='update_notification_preferences'),
    path('api/user-stats/', views.get_user_stats, name='get_user_stats'),
] 