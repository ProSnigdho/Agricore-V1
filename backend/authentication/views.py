
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from django.conf import settings

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from users.models import User
from users.serializers import CustomerRegistrationSerializer, UserSerializer
from .serializers import CustomTokenObtainPairSerializer


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Standard JWT login using email + password. Returns user info.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            try:
                email = request.data.get('email')
                user = User.objects.get(email=email)
                # Record activity
                from users.models import UserActivity
                client_ip = request.META.get('REMOTE_ADDR')
                UserActivity.objects.create(user=user, ip_address=client_ip)
            except Exception as e:
                print(f"Error recording activity: {e}")
        return response



class CustomTokenRefreshView(TokenRefreshView):
    """
    POST /api/auth/token/refresh/
    Refresh an expired access token using a valid refresh token.
    """
    permission_classes = [AllowAny]



class RegisterView(APIView):
    """
    POST /api/auth/register/
    Register a new customer account with email & password.
    Returns JWT tokens upon successful registration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)
        # Add custom claims
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['full_name'] = user.full_name

        return Response({
            'message': 'Registration successful.',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)



class GoogleLoginView(APIView):
    """
    POST /api/auth/google/
    Verify a Google ID token, register user if new, and return JWT tokens.
    Automatically assigns the 'customer' role to new Google sign-ups.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response(
                {'error': 'Google token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Verify the Google ID token
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )

            # Extract user info from verified Google token
            google_id = idinfo.get('sub')
            email = idinfo.get('email')
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            avatar_url = idinfo.get('picture', '')

            if not email:
                return Response(
                    {'error': 'Could not retrieve email from Google account.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Find or create the user
            user, created = User.objects.get_or_create(
                email=email.lower(),
                defaults={
                    'google_id': google_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'avatar_url': avatar_url,
                    'auth_provider': 'google',
                    'role': User.Role.CUSTOMER,
                },
            )

            # If user exists but hasn't linked Google, update fields
            if not created and not user.google_id:
                user.google_id = google_id
                user.avatar_url = avatar_url or user.avatar_url
                user.auth_provider = 'google'
                user.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            refresh['email'] = user.email
            refresh['role'] = user.role
            refresh['full_name'] = user.full_name

            # Record activity
            from users.models import UserActivity
            client_ip = request.META.get('REMOTE_ADDR')
            UserActivity.objects.create(user=user, ip_address=client_ip)

            return Response({
                'message': 'Google login successful.',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
                'is_new_user': created,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': f'Invalid Google token: {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return Response(
                {'error': f'Google authentication failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklist the refresh token to invalidate the session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Update UserActivity logout time
            from users.models import UserActivity
            latest_activity = UserActivity.objects.filter(user=request.user, logout_time__isnull=True).first()
            if latest_activity:
                latest_activity.logout_time = timezone.now()
                latest_activity.save()

            # Update last logout time on User model for backward compatibility
            request.user.last_logout = timezone.now()
            request.user.save()
            return Response(
                {'message': 'Logout successful.'},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {'message': 'Logout successful.'},
                status=status.HTTP_200_OK,
            )



class VerifyTokenView(APIView):
    """
    GET /api/auth/verify/
    Verify that the current access token is valid and return user info.
    Used by the frontend to check auth state on page load.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'valid': True,
            'user': UserSerializer(request.user).data,
        })


class UserActivityListView(APIView):
    """
    GET /api/auth/activities/
    Get login/logout activities for the current user.
    Admins can see all activities if 'user_id' is provided.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        from users.models import UserActivity
        from users.serializers import UserActivitySerializer

        if user_id and request.user.role == User.Role.ADMIN:
            activities = UserActivity.objects.filter(user_id=user_id)
        elif request.user.role == User.Role.ADMIN:
            activities = UserActivity.objects.all()
        else:
            activities = UserActivity.objects.filter(user=request.user)

        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)
