from django.db import models

class SystemSettings(models.Model):
    site_name = models.CharField(max_length=100, default="BookStore")
    site_description = models.TextField(blank=True)
    site_logo = models.ImageField(upload_to='settings/', null=True, blank=True)
    contact_email = models.EmailField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Social media links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    
    # System settings
    maintenance_mode = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SystemSettings.objects.exists():
            return
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create system settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
