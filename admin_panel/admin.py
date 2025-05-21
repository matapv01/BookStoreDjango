from django.contrib import admin
from .models import SystemSettings

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'maintenance_mode', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('site_name', 'site_description')
        }),
        ('Thông tin liên hệ', {
            'fields': ('contact_email', 'phone_number', 'address')
        }),
        ('Cài đặt hệ thống', {
            'fields': ('maintenance_mode', 'is_active')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Chỉ cho phép một instance
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Không cho phép xóa instance
        return False
