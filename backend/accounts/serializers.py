"""
Serializers for accounts app.
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, InviteToken


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'role_display', 'is_email_verified', 'can_access_admin_panel',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_email_verified']


class InviteTokenSerializer(serializers.ModelSerializer):
    """Serializer for InviteToken model."""
    
    creator_email = serializers.EmailField(source='creator.email', read_only=True)
    used_by_email = serializers.EmailField(source='used_by.email', read_only=True)
    
    class Meta:
        model = InviteToken
        fields = [
            'id', 'code', 'creator', 'creator_email',
            'used', 'used_by', 'used_by_email',
            'created_at', 'used_at'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'used_at']


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""
    
    email = serializers.EmailField(required=True)
    username = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    invite_token = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        
        # Validate invite token
        try:
            token = InviteToken.objects.get(code=attrs['invite_token'], used=False)
        except InviteToken.DoesNotExist:
            raise serializers.ValidationError({"invite_token": "Недействительный или уже использованный токен"})
        
        attrs['token'] = token
        return attrs
    
    def create(self, validated_data):
        token = validated_data.pop('token')
        validated_data.pop('password_confirm')
        validated_data.pop('invite_token')
        
        user = User.objects.create_user(**validated_data)
        token.use(user)
        
        # Generate email verification token
        import secrets
        verification_token = secrets.token_urlsafe(32)
        user.email_verification_token = verification_token
        user.is_email_verified = False
        user.save()
        
        # Send verification email
        self._send_verification_email(user, verification_token)
        
        # Create 3 invite tokens for new student
        if user.is_student:
            InviteToken.create_for_user(user, count=3)
        
        return user
    
    def _send_verification_email(self, user, token):
        """Send email verification email."""
        from .utils import send_verification_email
        request = self.context.get('request')
        send_verification_email(user, token, request)


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Неверный email или пароль")
            if not user.is_active:
                raise serializers.ValidationError("Аккаунт деактивирован")
            if user.is_blocked:
                raise serializers.ValidationError("Аккаунт заблокирован")
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError("Необходимо указать email и пароль")
        
        return attrs


class TokenPairSerializer(serializers.Serializer):
    """Serializer for JWT token pair."""
    
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
    
    @classmethod
    def get_tokens_for_user(cls, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }

