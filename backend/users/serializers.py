
from rest_framework import serializers
from .models import User, UserActivity


class UserActivitySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = UserActivity
        fields = ['id', 'user_email', 'full_name', 'login_time', 'logout_time', 'ip_address']


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for user data."""
    full_name = serializers.ReadOnlyField()

    activities = UserActivitySerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'date_joined', 'last_login', 'last_logout',
            'avatar_url', 'auth_provider', 'activities',
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'auth_provider']


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for customer self-registration."""
    password = serializers.CharField(
        write_only=True, min_length=8,
        style={'input_type': 'password'},
        help_text='Password must be at least 8 characters.',
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']

    def validate_email(self, value):
        """Ensure the email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate(self, attrs):
        """Ensure passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs

    def create(self, validated_data):
        """Create a new customer user."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=User.Role.CUSTOMER,
            auth_provider='email',
        )
        return user


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admins to view/manage all users."""

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'is_active', 'is_staff', 'date_joined', 'last_login', 'last_logout',
            'auth_provider', 'avatar_url',
        ]
        read_only_fields = ['id', 'date_joined', 'auth_provider']


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for users to update their own profile."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar_url']
