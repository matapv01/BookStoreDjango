import os
import django
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore.settings')
django.setup()

from main.models import Order

def update_order_statuses():
    print("Updating order statuses to Vietnamese...")
    
    # Map to standardize status codes (uppercase and known values)
    status_map = {
        'pending': 'PENDING',
        'processing': 'PROCESSING',
        'shipped': 'SHIPPED',
        'delivered': 'DELIVERED',
        'cancelled': 'CANCELLED',
        'Đang chờ xử lý': 'PENDING',
        'Đang xử lý': 'PROCESSING',
        'Đã giao cho vận chuyển': 'SHIPPED',
        'Đã giao hàng': 'DELIVERED',
        'Đã hủy': 'CANCELLED'
    }
    
    payment_map = {
        'Đang chờ thanh toán': 'PENDING',
        'paid': 'PAID',
        'failed': 'FAILED',
        'refunded': 'REFUNDED',
        'Đã thanh toán': 'PAID'
    }
=======
        'cancelled': 'CANCELLED',
        'Đang chờ xử lý': 'PENDING',
        'Đang xử lý': 'PROCESSING',
        'Đã giao cho vận chuyển': 'SHIPPED',
        'Đã giao hàng': 'DELIVERED',
        'Đã hủy': 'CANCELLED'
    }

    payment_map = {
        'Đang chờ thanh toán': 'Đang chờ thanh toán',
        'Đã thanh toán': 'Đã thanh toán',
    }
    
    for order in Order.objects.all():
        old_status = order.status
        old_display = order.get_status_display()
        
        # Normalize status to uppercase if it's lowercase
        if order.status.lower() in status_map:
            order.status = status_map[order.status.lower()]
            order.save()
            print(f"Updated order {order.id} from '{old_status}' to '{order.status}'")
        else:
            print(f"Order {order.id} already has correct status format: {order.status}")
        
        # Normalize payment status if needed
        if order.payment_status and order.payment_status.lower() in payment_map:
            old_payment = order.payment_status
            order.payment_status = payment_map[order.payment_status.lower()]
            order.save()
            print(f"Updated payment status for order {order.id} from '{old_payment}' to '{order.payment_status}'")
            
        print(f"Order {order.id}: status={order.status}, display={order.get_status_display()}")
        
    print("All orders processed!")

if __name__ == "__main__":
    update_order_statuses()
