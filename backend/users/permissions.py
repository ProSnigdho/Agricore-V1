"""
Custom DRF permissions for role-based access control.
Used across views to enforce ADMIN-only or CUSTOMER-only access.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to users with the ADMIN role."""
    message = 'Access denied. Administrator privileges required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsCustomer(BasePermission):
    """Allow access only to users with the CUSTOMER role."""
    message = 'Access denied. Customer account required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'customer'
        )
