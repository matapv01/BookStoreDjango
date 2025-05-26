from django.core.management.base import BaseCommand
from admin_panel.models import SystemSettings

class Command(BaseCommand):
    help = 'Khởi tạo cài đặt hệ thống'

    def handle(self, *args, **kwargs):
        if not SystemSettings.objects.exists():
            settings = SystemSettings.objects.create(
                site_name='BookStore',
                site_description='Nhà sách trực tuyến của bạn',
                contact_email='contact@bookstore.com',
                phone_number='',
                address='',
                maintenance_mode=False,
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS('Đã khởi tạo cài đặt hệ thống thành công')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Cài đặt hệ thống đã tồn tại')
            )