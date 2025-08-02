import random
import string
import uuid
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from .models import EmailVerificationToken, UserActivity
from django.utils import timezone
from datetime import timedelta

def generate_verification_token():
    """Generate a UUID verification token"""
    return str(uuid.uuid4())

def generate_2fa_code():
    """Generate a 6-digit 2FA code"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(user):
    """Send email verification link to user"""
    try:
        # Create verification token
        token = generate_verification_token()
        expires_at = timezone.now() + timedelta(hours=24)
        
        # Save token to database
        EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        # Prepare email content
        verification_url = f"http://127.0.0.1:8000/auth/verify-email/{token}/"
        
        subject = "Verify Your Email - Education System"
        html_content = render_to_string('authentication/email_verification.html', {
            'user': user,
            'verification_url': verification_url,
        })
        
        # Send email using Django's email backend
        from django.utils.html import strip_tags
        plain_text = strip_tags(html_content)
        
        send_mail(
            subject=subject,
            message=plain_text,
            from_email='digiskills2525@gmail.com',
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='email_verification',
            description='Verification email sent via Gmail SMTP',
            ip_address='127.0.0.1',
            user_agent='System',
            metadata={'email_sent': True, 'method': 'gmail_smtp'}
        )
        
        return True, "Verification email sent successfully via Gmail SMTP"
        
    except Exception as e:
        return False, f"Failed to send verification email: {str(e)}"

def send_2fa_email(user, code):
    """Send 2FA code to user"""
    try:
        subject = "Your 2FA Code - Education System"
        html_content = render_to_string('authentication/2fa_email.html', {
            'user': user,
            'code': code,
        })
        
        # Send email using Django's email backend
        from django.utils.html import strip_tags
        plain_text = strip_tags(html_content)
        
        send_mail(
            subject=subject,
            message=plain_text,
            from_email='digiskills2525@gmail.com',
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='two_factor_enabled',
            description='2FA code sent via Gmail SMTP',
            ip_address='127.0.0.1',
            user_agent='System',
            metadata={'2fa_sent': True, 'method': 'gmail_smtp'}
        )
        
        return True, "2FA code sent successfully via Gmail SMTP"
        
    except Exception as e:
        return False, f"Failed to send 2FA code: {str(e)}"

def verify_email_token(token):
    """Verify email token and mark user as verified"""
    try:
        verification_token = EmailVerificationToken.objects.get(
            token=token,
            used=False,
            expires_at__gt=timezone.now()
        )
        
        user = verification_token.user
        user.profile.email_verified = True
        user.profile.save()
        
        # Mark token as used
        verification_token.used = True
        verification_token.save()
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='email_verification',
            description='Email verified successfully',
            ip_address='127.0.0.1',
            user_agent='System',
            metadata={'email_verified': True}
        )
        
        return True, user, "Email verified successfully"
        
    except EmailVerificationToken.DoesNotExist:
        return False, None, "Invalid or expired verification token"
    except Exception as e:
        return False, None, f"Error verifying email: {str(e)}" 