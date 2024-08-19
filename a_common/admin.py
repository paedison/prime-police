from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from . import models


@admin.register(models.User)
class UserAdmin(AuthUserAdmin):
    list_display = list_display_links = ['id', 'email', 'username', 'joined_at', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff']
    fields = ['email', 'username', 'name', 'prime_id', 'joined_at', 'is_staff', 'is_active']
    fieldsets = None
    readonly_fields = ['email', 'username', 'name', 'prime_id', 'joined_at', 'is_staff']
    search_fields = ['email']
    ordering = ['id']

    class Media:
        css = {'all': ['css/admin_custom.css']}
