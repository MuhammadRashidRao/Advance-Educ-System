from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.models import User
import json

from .models import UserProfile, UserSession, LoginAttempt, PasswordResetToken, EmailVerificationToken, UserActivity
from .utils import send_verification_email, send_2fa_email, verify_email_token, generate_2fa_code
from .forms import (
    AdvancedUserCreationForm, AdvancedAuthenticationForm, AdvancedPasswordResetForm, 
    AdvancedSetPasswordForm, AdvancedUserProfileForm, AdvancedUserUpdateForm,
    TwoFactorSetupForm, EmailVerificationForm, PhoneVerificationForm,
    SecuritySettingsForm, NotificationPreferencesForm, SearchUserForm,
    TwoFactorVerificationForm
)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_user_activity(user, activity_type, description, request):
    UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata={'timestamp': timezone.now().isoformat()}
    )

def log_login_attempt(user, email, success, request):
    LoginAttempt.objects.create(
        user=user if success else None,
        email=email,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        attempt_type='success' if success else 'failed',
        success=success
    )

def home(request):
    return render(request, 'authentication/home.html')

class AdvancedLoginView(LoginView):
    template_name = 'authentication/login.html'
    form_class = AdvancedAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if user.is_active:
            # Check if user is a student and needs email verification
            if hasattr(user, 'profile') and user.profile.role == 'student':
                if not user.profile.email_verified:
                    messages.error(self.request, 'Please verify your email address before logging in. Check your email for the verification link.')
                    return self.form_invalid(form)
                
                # Generate and send 2FA code
                code = generate_2fa_code()
                success, message = send_2fa_email(user, code)
                
                if success:
                    # Store 2FA code in session for verification
                    self.request.session['2fa_code'] = code
                    self.request.session['2fa_user_id'] = user.id
                    self.request.session['2fa_expires'] = (timezone.now() + timedelta(minutes=10)).isoformat()
                    
                    messages.info(self.request, 'A 2FA code has been sent to your email. Please enter it to complete your login.')
                    return redirect('authentication:verify_2fa')
                else:
                    messages.error(self.request, f'Failed to send 2FA code: {message}')
                    return self.form_invalid(form)
            
            # For non-students, proceed with normal login
            login(self.request, user)
            
            # Log successful login
            log_login_attempt(user, user.email, True, self.request)
            log_user_activity(user, 'login', f'User logged in successfully', self.request)
            
            # Update user profile
            if hasattr(user, 'profile'):
                user.profile.last_login_ip = get_client_ip(self.request)
                user.profile.last_activity = timezone.now()
                user.profile.save()
            
            # Redirect based on user role
            if hasattr(user, 'profile') and user.profile.role == 'teacher':
                return redirect('authentication:teacher_dashboard')
            else:
                return redirect('authentication:dashboard')
        
        return super().form_valid(form)

    def form_invalid(self, form):
        # Log failed login attempt
        email = form.cleaned_data.get('username', '')
        log_login_attempt(None, email, False, self.request)
        return super().form_invalid(form)

class AdvancedRegisterView(CreateView):
    template_name = 'authentication/register.html'
    form_class = AdvancedUserCreationForm
    success_url = reverse_lazy('authentication:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Get the selected role from the form
        role = self.request.POST.get('role', 'student')
        
        # Update the user profile with the selected role
        if hasattr(self.object, 'profile'):
            self.object.profile.role = role
            self.object.profile.save()
        
        # Send verification email for students
        if role == 'student':
            success, message = send_verification_email(self.object)
            if success:
                messages.success(self.request, f'Account created successfully! Please check your email to verify your account before logging in.')
            else:
                messages.warning(self.request, f'Account created, but verification email could not be sent: {message}')
        else:
            messages.success(self.request, f'Account created successfully! You can now sign in as a {role}.')
        
        # Log user activity
        log_user_activity(self.object, 'login', f'New user registered with role: {role}', self.request)
        
        return response

class AdvancedLogoutView(LogoutView):
    next_page = reverse_lazy('authentication:login')
    http_method_names = ['get', 'post']  # Allow both GET and POST requests

    def dispatch(self, request, *args, **kwargs):
        try:
            if request.user.is_authenticated:
                log_user_activity(request.user, 'logout', 'User logged out', request)
        except Exception as e:
            # Log the error but don't prevent logout
            print(f"Error logging logout activity: {e}")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Ensure logout happens even with GET request
        return self.post(request, *args, **kwargs)

class AdvancedPasswordResetView(PasswordResetView):
    template_name = 'authentication/password_reset.html'
    email_template_name = 'authentication/password_reset_email.html'
    subject_template_name = 'authentication/password_reset_subject.txt'
    success_url = reverse_lazy('authentication:password_reset_done')

class AdvancedPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'authentication/password_reset_done.html'

class AdvancedPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'authentication/password_reset_confirm.html'
    success_url = reverse_lazy('authentication:password_reset_complete')

class AdvancedPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'authentication/password_reset_complete.html'

class AdvancedUserProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'authentication/profile.html'
    context_object_name = 'user'

    def get_object(self):
        return self.request.user

class AdvancedUserUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = AdvancedUserUpdateForm
    template_name = 'authentication/profile_edit.html'
    success_url = reverse_lazy('authentication:profile')

    def get_object(self):
        return self.request.user.profile

class TeacherRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'teacher'

@login_required
def dashboard(request):
    user = request.user
    if hasattr(user, 'profile') and user.profile.role == 'teacher':
        return redirect('authentication:teacher_dashboard')
    
    # Regular dashboard for non-teachers
    context = {
        'user': user,
        'recent_activities': UserActivity.objects.filter(user=user).order_by('-timestamp')[:5],
        'active_sessions': UserSession.objects.filter(user=user, is_active=True),
    }
    return render(request, 'authentication/dashboard.html', context)

@login_required
def teacher_dashboard(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teacher':
        messages.error(request, 'Access denied. Teacher role required.')
        return redirect('authentication:dashboard')
    
    context = {
        'user': request.user,
        'recent_activities': UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:5],
        'active_sessions': UserSession.objects.filter(user=request.user, is_active=True),
    }
    return render(request, 'authentication/teacher_dashboard.html', context)

@login_required
def teacher_live_session(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teacher':
        messages.error(request, 'Access denied. Teacher role required.')
        return redirect('authentication:dashboard')
    
    context = {
        'user': request.user,
        'session_id': request.GET.get('session_id', 'default'),
    }
    return render(request, 'authentication/teacher_live_session.html', context)

@login_required
def teacher_session_management(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'teacher':
        messages.error(request, 'Access denied. Teacher role required.')
        return redirect('authentication:dashboard')
    
    context = {
        'user': request.user,
        'sessions': [],  # You can add session management logic here
    }
    return render(request, 'authentication/teacher_session_management.html', context)

@login_required
def security_settings(request):
    if request.method == 'POST':
        form = SecuritySettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Security settings updated successfully.')
            return redirect('authentication:security_settings')
    else:
        form = SecuritySettingsForm(instance=request.user)
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'authentication/security_settings.html', context)

@login_required
def notification_preferences(request):
    if request.method == 'POST':
        form = NotificationPreferencesForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification preferences updated successfully.')
            return redirect('authentication:notification_preferences')
    else:
        form = NotificationPreferencesForm(instance=request.user.profile)
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'authentication/notification_preferences.html', context)

@login_required
def user_activity(request):
    activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'user': request.user,
    }
    return render(request, 'authentication/user_activity.html', context)

@login_required
def session_management(request):
    sessions = UserSession.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'sessions': sessions,
        'user': request.user,
    }
    return render(request, 'authentication/session_management.html', context)

@login_required
def email_verification(request):
    if request.user.profile.email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('authentication:dashboard')
    
    context = {
        'user': request.user,
    }
    return render(request, 'authentication/email_verification.html', context)

def verify_email(request, token):
    """Verify email token and redirect to login"""
    success, user, message = verify_email_token(token)
    
    if success:
        messages.success(request, 'Email verified successfully! You can now log in.')
    else:
        messages.error(request, message)
    
    return redirect('authentication:login')

def verify_2fa(request):
    """Handle 2FA verification"""
    if request.method == 'POST':
        form = TwoFactorVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            stored_code = request.session.get('2fa_code')
            user_id = request.session.get('2fa_user_id')
            expires = request.session.get('2fa_expires')
            
            # Check if 2FA session is valid
            if not all([stored_code, user_id, expires]):
                messages.error(request, '2FA session expired. Please try logging in again.')
                return redirect('authentication:login')
            
            # Check if code has expired
            if timezone.now() > timezone.datetime.fromisoformat(expires):
                messages.error(request, '2FA code has expired. Please try logging in again.')
                return redirect('authentication:login')
            
            # Verify code
            if code == stored_code:
                # Get user and log them in
                try:
                    user = User.objects.get(id=user_id)
                    login(request, user)
                    
                    # Clear 2FA session data
                    del request.session['2fa_code']
                    del request.session['2fa_user_id']
                    del request.session['2fa_expires']
                    
                    # Log successful login
                    log_login_attempt(user, user.email, True, request)
                    log_user_activity(user, 'login', f'User logged in successfully with 2FA', request)
                    
                    # Update user profile
                    if hasattr(user, 'profile'):
                        user.profile.last_login_ip = get_client_ip(request)
                        user.profile.last_activity = timezone.now()
                        user.profile.save()
                    
                    messages.success(request, 'Login successful! Welcome back.')
                    return redirect('authentication:dashboard')
                    
                except User.DoesNotExist:
                    messages.error(request, 'User not found. Please try logging in again.')
                    return redirect('authentication:login')
            else:
                messages.error(request, 'Invalid 2FA code. Please try again.')
    else:
        form = TwoFactorVerificationForm()
    
    return render(request, 'authentication/verify_2fa.html', {'form': form})

@user_passes_test(lambda u: u.is_staff)
def user_management(request):
    users = User.objects.select_related('profile').all()
    search_form = SearchUserForm(request.GET)
    
    if search_form.is_valid():
        query = search_form.cleaned_data.get('query', '')
        if query:
            users = users.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(profile__role__icontains=query)
            )
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
    }
    return render(request, 'authentication/user_management.html', context)

@user_passes_test(lambda u: u.is_staff)
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:10]
    login_attempts = LoginAttempt.objects.filter(user=user).order_by('-timestamp')[:10]
    
    context = {
        'user_detail': user,
        'activities': activities,
        'login_attempts': login_attempts,
    }
    return render(request, 'authentication/user_detail.html', context)

@require_POST
@csrf_exempt
def update_notification_preferences(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        profile = request.user.profile
        profile.notification_preferences.update(data)
        profile.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_user_stats(request):
    user = request.user
    stats = {
        'total_activities': UserActivity.objects.filter(user=user).count(),
        'total_sessions': UserSession.objects.filter(user=user).count(),
        'active_sessions': UserSession.objects.filter(user=user, is_active=True).count(),
        'login_attempts': LoginAttempt.objects.filter(user=user).count(),
        'successful_logins': LoginAttempt.objects.filter(user=user, success=True).count(),
    }
    
    return JsonResponse(stats)
