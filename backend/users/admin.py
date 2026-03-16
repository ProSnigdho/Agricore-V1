from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'auth_provider', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'auth_provider']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
