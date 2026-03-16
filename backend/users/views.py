
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    UserSerializer,
    AdminUserSerializer,
    UpdateProfileSerializer,
)
from .permissions import IsAdmin, IsCustomer


class ProfileView(APIView):
    """Retrieve or update current user's profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UpdateProfileSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class AdminDashboardView(APIView):
    """Admin dashboard stats and recent users."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from .models import UserActivity
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_users = User.objects.count()
        total_customers = User.objects.filter(role=User.Role.CUSTOMER).count()
        total_admins = User.objects.filter(role=User.Role.ADMIN).count()
        
        daily_logins = UserActivity.objects.filter(login_time__gte=today_start).count()
        monthly_logins = UserActivity.objects.filter(login_time__gte=month_start).count()

        recent_users = User.objects.order_by('-date_joined')[:5]

        return Response({
            'stats': {
                'total_users': total_users,
                'total_customers': total_customers,
                'total_admins': total_admins,
                'daily_logins': daily_logins,
                'monthly_logins': monthly_logins,
            },
            'recent_users': UserSerializer(recent_users, many=True).data,
        })


class AdminUserListView(generics.ListAPIView):
    """List all users for admin review."""
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all()


class CustomerDashboardView(APIView):
    """Dashboard data for customers."""
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'message': f'Welcome back, {request.user.full_name or request.user.email}!',
            'user': serializer.data,
        })


class AdminUpdateRoleView(APIView):
    """Promote or demote a user role."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        user_id = request.data.get('user_id')
        new_role = request.data.get('role')

        if not user_id or not new_role:
            return Response(
                {'error': 'User ID and Role are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_role not in [User.Role.ADMIN, User.Role.CUSTOMER]:
            return Response(
                {'error': 'Invalid role.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_user = User.objects.get(id=user_id)
            target_user.role = new_role
            # Also update is_staff for admin access to Django admin if needed
            target_user.is_staff = (new_role == User.Role.ADMIN)
            target_user.save()
            
            return Response({
                'message': f'User {target_user.email} updated to {new_role}.',
                'user': AdminUserSerializer(target_user).data
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
