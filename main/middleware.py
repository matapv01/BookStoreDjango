from django.shortcuts import render
from admin_panel.models import SystemSettings
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

class WebsiteStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Danh sách các URL được phép truy cập trong chế độ bảo trì
        self.allowed_urls = [
            '/admin-panel/login/',
            '/admin-panel/logout/',
            '/admin/login/',
            '/admin/logout/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        # Kiểm tra nếu URL hiện tại nằm trong danh sách được phép
        if any(request.path.startswith(url) for url in self.allowed_urls):
            return self.get_response(request)

        # Bỏ qua middleware cho các URL của admin
        if request.path.startswith('/admin/') or request.path.startswith('/admin_panel/'):
            return self.get_response(request)

        # Lấy cài đặt hệ thống
        settings = SystemSettings.get_settings()

        # Kiểm tra nếu website đang trong chế độ bảo trì
        if settings.maintenance_mode:
            # Cho phép admin truy cập
            if request.user.is_staff:
                return self.get_response(request)
            # Hiển thị trang bảo trì cho người dùng thông thường
            return render(request, 'maintenance.html', {'system_settings': settings})

        # Kiểm tra nếu website không hoạt động
        if not settings.is_active:
            # Cho phép admin truy cập
            if request.user.is_staff:
                return self.get_response(request)
            # Hiển thị trang bảo trì cho người dùng thông thường
            return render(request, 'maintenance.html', {'system_settings': settings})

        return self.get_response(request) 