"""
Utility functions for accounts app.
"""
import secrets
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

SPAM_NOTICE = '\n\n⚠️ ВАЖНО: Если вы не видите письмо во входящих, пожалуйста, проверьте папку "Спам".'


def send_verification_email(user, token, request=None):
    """Send email verification email with spam notice."""
    if request:
        base_url = request.build_absolute_uri('/')
    else:
        base_url = 'http://localhost:3000/'
    
    verification_url = f"{base_url}verify-email?token={token}"
    
    subject = 'Подтверждение email адреса'
    message = f'''Здравствуйте, {user.username}!

Для подтверждения вашего email адреса перейдите по ссылке:
{verification_url}

Если вы не регистрировались на нашем сайте, проигнорируйте это письмо.

С уважением,
Команда Студенческой базы знаний{SPAM_NOTICE}
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL or 'noreply@university.local',
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.warning(f"Failed to send verification email to {user.email}: {e}")
        # For development, print to console
        print(f"\n{'='*60}")
        print(f"EMAIL VERIFICATION TOKEN for {user.email}:")
        print(f"Token: {token}")
        print(f"Verification URL: {verification_url}")
        print(f"{'='*60}\n")
        return False


def send_password_reset_email(user, token, request=None):
    """Send password reset email with spam notice."""
    if request:
        base_url = request.build_absolute_uri('/').replace('/api/', '/')
    else:
        base_url = 'http://localhost:3000/'
    
    reset_url = f"{base_url}reset-password?token={token}"
    
    subject = 'Восстановление пароля'
    message = f'''Здравствуйте, {user.username}!

Вы запросили восстановление пароля. Для сброса пароля перейдите по ссылке:
{reset_url}

Если вы не запрашивали восстановление пароля, проигнорируйте это письмо.

Ссылка действительна в течение 24 часов.

С уважением,
Команда Студенческой базы знаний{SPAM_NOTICE}
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL or 'noreply@university.local',
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.warning(f"Failed to send password reset email to {user.email}: {e}")
        # For development, print to console
        print(f"\n{'='*60}")
        print(f"PASSWORD RESET TOKEN for {user.email}:")
        print(f"Token: {token}")
        print(f"Reset URL: {reset_url}")
        print(f"{'='*60}\n")
        return False

