"""
URL configuration for the Authentication app.
"""

from django.urls import path
from .views import (
    LoginView,
    CustomTokenRefreshView,
    RegisterView,
    GoogleLoginView,
    LogoutView,
    VerifyTokenView,
    UserActivityListView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('google/', GoogleLoginView.as_view(), name='auth-google'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('verify/', VerifyTokenView.as_view(), name='auth-verify'),
    path('activities/', UserActivityListView.as_view(), name='auth-activities'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),
]
