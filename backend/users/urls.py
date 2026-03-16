"""
URL configuration for the Users app.
"""

from django.urls import path
from .views import (
    ProfileView,
    AdminDashboardView,
    AdminUserListView,
    CustomerDashboardView,
    AdminUpdateRoleView,
)

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/update-role/', AdminUpdateRoleView.as_view(), name='admin-update-role'),
    path('customer/dashboard/', CustomerDashboardView.as_view(), name='customer-dashboard'),
]
