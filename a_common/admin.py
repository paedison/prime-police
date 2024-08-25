from django.contrib import admin
from django.contrib.auth import admin as auth_admin, models as auth_models
from unfold.admin import ModelAdmin

from . import models


@admin.register(models.User)
class UserAdmin(ModelAdmin, auth_admin.UserAdmin):
    list_display = list_display_links = ['id', 'email', 'username', 'joined_at', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff']
    readonly_fields = ['email', 'username', 'name', 'prime_id', 'joined_at', 'last_login', 'is_staff']
    fields = readonly_fields + ['is_active', 'groups']
    fieldsets = None
    search_fields = ['email']
    ordering = ['id']


admin.site.unregister(auth_models.Group)


@admin.register(auth_models.Group)
class GroupAdmin(ModelAdmin, auth_admin.GroupAdmin):
    pass
