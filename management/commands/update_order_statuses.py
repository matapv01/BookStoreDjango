from django.core.management.base import BaseCommand
from main.models import Order

class Command(BaseCommand):
    help = 'Updates order statuses to use Vietnamese strings.'

    def handle(self, *args, **kwargs):
        for order in Order.objects.all():
            # Update status
            if order.status == 'PENDING':
                order.status = 'Đang chờ xử lý'
            elif order.status == 'PROCESSING':
                order.status = 'Đang xử lý'
            elif order.status == 'SHIPPED':
                order.status = 'Đã giao cho vận chuyển'
            elif order.status == 'DELIVERED':
                order.status = 'Đã giao hàng'
            elif order.status == 'CANCELLED':
                order.status = 'Đã hủy'
            
            order.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated order {order.order_number}'))
        self.stdout.write(self.style.SUCCESS('Successfully updated all order statuses.'))
