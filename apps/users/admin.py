from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'phone', 'referral_code', 'is_blocked',
                    'is_active', 'date_joined']
    list_filter = ['is_blocked', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone', 'referral_code']
    readonly_fields = ['id', 'referral_code', 'date_joined']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Gaming Platform', {'fields': ('phone', 'referral_code', 'referred_by', 'is_blocked', 'avatar')}),
    )
    actions = ['block_users', 'unblock_users']

    @admin.action(description='Block selected users')
    def block_users(self, request, queryset):
        queryset.update(is_blocked=True)

    @admin.action(description='Unblock selected users')
    def unblock_users(self, request, queryset):
        queryset.update(is_blocked=False)
