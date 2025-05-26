from django.db import models
from django.core.exceptions import ValidationError

class SystemSettings(models.Model):
    site_name = models.CharField(max_length=100, default="BookStore", verbose_name="Tên website")
    site_description = models.TextField(blank=True, verbose_name="Mô tả website")
    contact_email = models.EmailField(max_length=100, blank=True, verbose_name="Email liên hệ")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại")
    address = models.TextField(blank=True, verbose_name="Địa chỉ")
    
    # System settings
    maintenance_mode = models.BooleanField(default=False, verbose_name="Chế độ bảo trì", 
        help_text="Khi bật chế độ bảo trì, website sẽ hiển thị trang bảo trì cho người dùng thông thường")
    is_active = models.BooleanField(default=True, verbose_name="Website hoạt động", 
        help_text="Khi tắt, website sẽ tự động chuyển sang chế độ bảo trì")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Cài đặt hệ thống"
        verbose_name_plural = "Cài đặt hệ thống"

    def __str__(self):
        return self.site_name

    def clean(self):
        # Đảm bảo chỉ một trong hai trạng thái được bật
        if self.maintenance_mode and self.is_active:
            raise ValidationError("Website không thể vừa ở chế độ bảo trì vừa hoạt động bình thường")
        
        # Đảm bảo luôn có một trạng thái được bật
        if not self.maintenance_mode and not self.is_active:
            raise ValidationError("Website phải ở một trong hai trạng thái: hoạt động hoặc bảo trì")

    def save(self, *args, **kwargs):
        # Đảm bảo chỉ có một instance tồn tại
        if not self.pk and SystemSettings.objects.exists():
            return
        
        # Nếu bật chế độ bảo trì, tự động tắt is_active
        if self.maintenance_mode:
            self.is_active = False
        # Nếu tắt is_active, tự động bật chế độ bảo trì
        elif not self.is_active:
            self.maintenance_mode = True
        
        self.full_clean()  # Gọi clean() để kiểm tra validation
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create system settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_order', 'Đơn hàng mới'),
        ('order_cancelled', 'Đơn hàng bị hủy'),
        ('order_status', 'Cập nhật trạng thái đơn hàng'),
        ('payment_status', 'Cập nhật trạng thái thanh toán'),
    ]

    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, blank=True)  # URL để chuyển hướng khi click vào thông báo

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Thông báo'
        verbose_name_plural = 'Thông báo'

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    @classmethod
    def create_order_notification(cls, order, notification_type):
        """Tạo thông báo cho đơn hàng"""
        if notification_type == 'new_order':
            message = f"Đơn hàng mới #{order.id} từ {order.user.get_full_name() or order.user.username}"
            link = f"/admin-panel/orders/{order.id}/"
        elif notification_type == 'order_cancelled':
            message = f"Đơn hàng #{order.id} đã bị hủy"
            link = f"/admin-panel/orders/{order.id}/"
        elif notification_type == 'order_status':
            message = f"Đơn hàng #{order.id} đã được cập nhật trạng thái thành {order.get_status_display()}"
            link = f"/admin-panel/orders/{order.id}/"
        elif notification_type == 'payment_status':
            message = f"Đơn hàng #{order.id} đã được cập nhật trạng thái thanh toán thành {order.payment_status}"
            link = f"/admin-panel/orders/{order.id}/"
        else:
            return None

        return cls.objects.create(
            message=message,
            notification_type=notification_type,
            link=link
        )
