"""
User and Invite Token models.
"""
import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.utils import timezone


class User(AbstractUser):
    """Custom User model with roles."""
    
    class Role(models.TextChoices):
        STUDENT = 'student', 'Студент'
        MODERATOR = 'moderator', 'Модератор'
        ADMIN = 'admin', 'Администратор'
    
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name='Email'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name='Роль'
    )
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name='Email подтвержден'
    )
    email_verification_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Токен верификации email'
    )
    password_reset_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name='Токен сброса пароля'
    )
    password_reset_token_created = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата создания токена сброса пароля'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    is_blocked = models.BooleanField(
        default=False,
        verbose_name='Заблокирован'
    )
    can_access_admin_panel = models.BooleanField(
        default=False,
        verbose_name='Доступ к админ-панели'
    )
    group = models.ForeignKey(
        'schedule.Group',
        on_delete=models.SET_NULL,
        related_name='students',
        null=True,
        blank=True,
        verbose_name='Группа'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
    
    @property
    def is_moderator(self):
        return self.role == self.Role.MODERATOR
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def can_moderate(self):
        return self.is_moderator or self.is_admin
    
    def can_manage_users(self):
        return self.is_admin


class InviteToken(models.Model):
    """Invite token for user registration."""
    
    code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='Код токена'
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_invite_tokens',
        verbose_name='Создатель токена'
    )
    used = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Использован'
    )
    used_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='used_invite_tokens',
        null=True,
        blank=True,
        verbose_name='Использован пользователем'
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата использования'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Инвайт-токен'
        verbose_name_plural = 'Инвайт-токены'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'used']),
            models.Index(fields=['creator', 'used']),
        ]
    
    def __str__(self):
        status = "использован" if self.used else "активен"
        return f"Токен {self.code[:8]}... ({status})"
    
    @classmethod
    def generate_code(cls):
        """Generate a unique invite token code."""
        while True:
            code = secrets.token_urlsafe(32)
            if not cls.objects.filter(code=code).exists():
                return code
    
    @classmethod
    def create_for_user(cls, creator, count=1):
        """Create invite tokens for a user."""
        tokens = []
        for _ in range(count):
            token = cls.objects.create(
                code=cls.generate_code(),
                creator=creator
            )
            tokens.append(token)
        return tokens
    
    def use(self, user):
        """Mark token as used by a user."""
        if self.used:
            raise ValueError("Token already used")
        self.used = True
        self.used_by = user
        self.used_at = timezone.now()
        self.save()
    
    @classmethod
    def get_active_tokens_for_user(cls, user):
        """Get active (unused) invite tokens for a user."""
        return cls.objects.filter(creator=user, used=False)
    
    @classmethod
    def get_referral_chain(cls, user):
        """Get referral chain for a user (who invited whom)."""
        chain = []
        current_user = user
        
        while current_user:
            used_token = cls.objects.filter(used_by=current_user).first()
            if used_token:
                chain.append({
                    'user': current_user,
                    'invited_by': used_token.creator,
                    'used_at': used_token.used_at
                })
                current_user = used_token.creator
            else:
                break
        
        return chain

