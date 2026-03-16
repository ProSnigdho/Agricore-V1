"""
Custom JWT serializers for AgriCore.
Adds role and user data to the token response.
"""

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from users.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that includes user role and profile in the token claims
    and in the response body.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims to the JWT payload
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user info to the response body
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'avatar_url': self.user.avatar_url,
            'auth_provider': self.user.auth_provider,
        }
        return data


class GoogleLoginSerializer(serializers.Serializer):
    """Serializer for Google OAuth token verification."""
    token = serializers.CharField(
        required=True,
        help_text='Google OAuth ID token received from frontend.',
    )
