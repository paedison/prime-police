from django.contrib import admin
from django.contrib.auth import admin as auth_admin, models as auth_models
from unfold.admin import ModelAdmin

from . import models


@admin.register(models.User)
class UserAdmin(ModelAdmin, auth_admin.UserAdmin):
    readonly_fields = ['id', 'email', 'name', 'prime', 'joined_date', 'last_login_date', 'is_staff']
    list_display = list_display_links = readonly_fields + ['is_active']
    fields = readonly_fields + ['is_active', 'groups']
    list_filter = ['is_active', 'is_staff']
    fieldsets = None
    search_fields = ['email']
    ordering = ['id']

    def prime(self, obj):
        return obj.prime_id

    def joined_date(self, obj):
        if obj.joined_at:
            return obj.joined_at.strftime('%Y/%m/%d')
        return '-'

    def last_login_date(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%Y/%m/%d')
        return '-'

    prime.short_description = '프라임ID'
    joined_date.short_description = '가입일'
    last_login_date.short_description = '최근 접속일'


admin.site.unregister(auth_models.Group)


@admin.register(auth_models.Group)
class GroupAdmin(ModelAdmin, auth_admin.GroupAdmin):
    pass
