from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    UserProfile, UserSession, LoginAttempt, PasswordResetToken, 
    EmailVerificationToken, UserActivity
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'
    fields = (
        'role', 'is_verified', 'is_active', 'phone_number', 'date_of_birth', 
        'gender', 'email_verified', 'phone_verified', 'two_factor_enabled'
    )


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'full_name', 'role', 'is_verified', 'is_active', 'date_joined', 'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'profile__role', 'profile__is_verified')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__phone_number')
    ordering = ('-date_joined',)
    
    def full_name(self, obj):
        return obj.profile.full_name
    full_name.short_description = 'Full Name'
    
    def role(self, obj):
        return obj.profile.get_role_display()
    role.short_description = 'Role'
    
    def is_verified(self, obj):
        return obj.profile.get_is_verified_display()
    is_verified.short_description = 'Verification Status'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_verified', 'email_verified', 'phone_verified', 'two_factor_enabled', 'created_at')
    list_filter = ('role', 'is_verified', 'email_verified', 'phone_verified', 'two_factor_enabled', 'created_at', 'gender')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'last_activity', 'last_login_ip')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'is_verified', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email_verified', 'phone_verified')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'gender', 'bio')
        }),
        ('Address Information', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Profile Information', {
            'fields': ('profile_picture', 'website')
        }),
        ('Security Settings', {
            'fields': ('two_factor_enabled', 'last_password_change')
        }),
        ('Preferences', {
            'fields': ('language', 'timezone', 'notification_preferences')
        }),
        ('Social Login', {
            'fields': ('social_login_provider', 'social_login_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_activity', 'last_login_ip'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'created_at', 'last_activity', 'is_active')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__username', 'user__email', 'ip_address', 'session_key')
    readonly_fields = ('session_key', 'created_at', 'last_activity')
    ordering = ('-created_at',)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'ip_address', 'attempt_type', 'success', 'timestamp')
    list_filter = ('attempt_type', 'success', 'timestamp')
    search_fields = ('email', 'user__username', 'ip_address')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_short', 'created_at', 'expires_at', 'used', 'ip_address')
    list_filter = ('used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('token', 'created_at', 'expires_at')
    ordering = ('-created_at',)
    
    def token_short(self, obj):
        return str(obj.token)[:8] + '...'
    token_short.short_description = 'Token'
    
    def has_add_permission(self, request):
        return False


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_short', 'created_at', 'expires_at', 'used')
    list_filter = ('used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('token', 'created_at', 'expires_at')
    ordering = ('-created_at',)
    
    def token_short(self, obj):
        return str(obj.token)[:8] + '...'
    token_short.short_description = 'Token'
    
    def has_add_permission(self, request):
        return False


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'ip_address', 'timestamp', 'description_short')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'user__email', 'description', 'ip_address')
    readonly_fields = ('timestamp', 'metadata_display')
    ordering = ('-timestamp',)
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def metadata_display(self, obj):
        if obj.metadata:
            return format_html('<pre>{}</pre>', str(obj.metadata))
        return '-'
    metadata_display.short_description = 'Metadata'
    
    def has_add_permission(self, request):
        return False


# Custom admin site configuration
admin.site.site_header = "Education System Administration"
admin.site.site_title = "Education System Admin"
admin.site.index_title = "Welcome to Education System Administration"
