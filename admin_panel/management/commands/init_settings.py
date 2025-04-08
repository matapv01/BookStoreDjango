from django.core.management.base import BaseCommand
from admin_panel.models import SystemSettings

class Command(BaseCommand):
    help = 'Initialize system settings'

    def handle(self, *args, **kwargs):
        if not SystemSettings.objects.exists():
            settings = SystemSettings.objects.create(
                site_name='BookStore',
                site_description='Your Online Bookstore',
                contact_email='contact@bookstore.com',
                phone_number='',
                address='',
                facebook_url='#',
                twitter_url='#',
                instagram_url='#',
                maintenance_mode=False,
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS('Successfully created system settings')
            )
        else:
            self.stdout.write(
                self.style.WARNING('System settings already exist')
            )