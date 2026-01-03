"""
Views for accounts app.
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import secrets
from .models import InviteToken
from .serializers import (
    UserSerializer, InviteTokenSerializer,
    RegisterSerializer, LoginSerializer, TokenPairSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            # Log validation errors for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Registration validation errors: {serializer.errors}")
            logger.error(f"Request data: {request.data}")
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        tokens = TokenPairSerializer.get_tokens_for_user(user)
        
        return Response({
            'message': 'Регистрация успешна. Проверьте email для подтверждения.',
            **tokens
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """User login endpoint."""
    
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        tokens = TokenPairSerializer.get_tokens_for_user(user)
        
        return Response(tokens, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile."""
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_invite_tokens(request):
    """Get current user's invite tokens (both active and used)."""
    tokens = InviteToken.objects.filter(creator=request.user).order_by('-created_at')
    serializer = InviteTokenSerializer(tokens, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_invite_tokens(request):
    """Generate new invite tokens."""
    user = request.user
    
    # Only students can generate tokens (they have limited amount)
    # Admins have unlimited tokens
    if user.is_student:
        active_count = InviteToken.get_active_tokens_for_user(user).count()
        if active_count >= 3:
            return Response(
                {'error': 'У вас уже есть максимальное количество активных токенов (3)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        count = min(3 - active_count, int(request.data.get('count', 1)))
    else:
        # Admins and moderators can generate unlimited tokens
        count = int(request.data.get('count', 1))
    
    tokens = InviteToken.create_for_user(user, count=count)
    serializer = InviteTokenSerializer(tokens, many=True)
    
    return Response({
        'message': f'Создано токенов: {len(tokens)}',
        'tokens': serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def referral_chain(request):
    """Get referral chain for current user."""
    chain = InviteToken.get_referral_chain(request.user)
    return Response({
        'chain': [
            {
                'user': UserSerializer(item['user']).data,
                'invited_by': UserSerializer(item['invited_by']).data,
                'used_at': item['used_at']
            }
            for item in chain
        ]
    })


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_invite_token(request, token_id):
    """Delete invite token (admin only)."""
    if not request.user.is_admin:
        return Response(
            {'error': 'Только администраторы могут удалять токены'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        token = InviteToken.objects.get(id=token_id)
        if token.used:
            return Response(
                {'error': 'Нельзя удалить использованный токен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        token.delete()
        return Response({'message': 'Токен удален'})
    except InviteToken.DoesNotExist:
        return Response(
            {'error': 'Токен не найден'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """Check if email is available for registration."""
    email = request.query_params.get('email', '').strip()
    if not email:
        return Response({'available': False, 'error': 'Email не указан'}, status=status.HTTP_400_BAD_REQUEST)
    
    exists = User.objects.filter(email__iexact=email).exists()
    return Response({'available': not exists})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_username_availability(request):
    """Check if username is available for registration."""
    username = request.query_params.get('username', '').strip()
    if not username:
        return Response({'available': False, 'error': 'Имя пользователя не указано'}, status=status.HTTP_400_BAD_REQUEST)
    
    exists = User.objects.filter(username__iexact=username).exists()
    return Response({'available': not exists})


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def check_invite_token(request):
    """Check if invite token is valid."""
    token_code = request.query_params.get('token', '').strip()
    if not token_code:
        return Response({'valid': False, 'error': 'Токен не указан'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        token = InviteToken.objects.get(code=token_code, used=False)
        return Response({'valid': True})
    except InviteToken.DoesNotExist:
        return Response({'valid': False, 'error': 'Недействительный или уже использованный токен'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email(request):
    """Verify user email by token."""
    token = request.data.get('token', '').strip()
    if not token:
        return Response(
            {'error': 'Токен не указан'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email_verification_token=token)
        if user.is_email_verified:
            return Response(
                {'message': 'Email уже подтвержден'},
                status=status.HTTP_200_OK
            )
        
        user.is_email_verified = True
        user.email_verification_token = None
        user.save()
        
        return Response({
            'message': 'Email успешно подтвержден',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(
            {'error': 'Недействительный токен подтверждения'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resend_verification_email(request):
    """Resend email verification token."""
    user = request.user
    
    if user.is_email_verified:
        return Response(
            {'message': 'Email уже подтвержден'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate new token
    import secrets
    verification_token = secrets.token_urlsafe(32)
    user.email_verification_token = verification_token
    user.save()
    
    # Send verification email
    from .utils import send_verification_email
    
    send_verification_email(user, verification_token, request)
    
    return Response({
        'message': 'Письмо с подтверждением отправлено на ваш email'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    """Request password reset - sends email with reset token."""
    email = request.data.get('email', '').strip()
    
    if not email:
        return Response(
            {'error': 'Email не указан'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email__iexact=email)
        
        # Only allow password reset for verified emails
        if not user.is_email_verified:
            return Response(
                {'error': 'Сначала подтвердите ваш email адрес'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        user.password_reset_token = reset_token
        user.password_reset_token_created = timezone.now()
        user.save()
        
        # Send password reset email
        from .utils import send_password_reset_email
        send_password_reset_email(user, reset_token, request)
        
        # Always return success message (don't reveal if email exists)
        return Response({
            'message': 'Если указанный email зарегистрирован и подтвержден, письмо с инструкциями отправлено'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        # Don't reveal if email doesn't exist
        return Response({
            'message': 'Если указанный email зарегистрирован и подтвержден, письмо с инструкциями отправлено'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    """Confirm password reset with token and new password."""
    token = request.data.get('token', '').strip()
    new_password = request.data.get('password', '').strip()
    password_confirm = request.data.get('password_confirm', '').strip()
    
    if not token:
        return Response(
            {'error': 'Токен не указан'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not new_password:
        return Response(
            {'error': 'Новый пароль не указан'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_password != password_confirm:
        return Response(
            {'error': 'Пароли не совпадают'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 8:
        return Response(
            {'error': 'Пароль должен содержать минимум 8 символов'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(password_reset_token=token)
        
        # Check if token is expired (24 hours)
        if user.password_reset_token_created:
            token_age = timezone.now() - user.password_reset_token_created
            if token_age > timedelta(hours=24):
                user.password_reset_token = None
                user.password_reset_token_created = None
                user.save()
                return Response(
                    {'error': 'Токен сброса пароля истек. Запросите новый'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Set new password
        user.set_password(new_password)
        user.password_reset_token = None
        user.password_reset_token_created = None
        user.save()
        
        return Response({
            'message': 'Пароль успешно изменен'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Недействительный токен сброса пароля'},
            status=status.HTTP_400_BAD_REQUEST
        )

