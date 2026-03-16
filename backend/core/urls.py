"""
AgriCore URL Configuration
Root URL dispatcher that routes to authentication and user endpoints.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/users/', include('users.urls')),
]
