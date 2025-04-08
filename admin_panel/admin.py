from django.contrib import admin
from .models import SystemSettings

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'maintenance_mode', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'site_description', 'site_logo')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'phone_number', 'address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url')
        }),
        ('System Settings', {
            'fields': ('maintenance_mode', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Only allow one instance
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the settings instance
        return False
