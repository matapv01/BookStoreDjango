from django.db import migrations

def fix_statuses(apps, schema_editor):
    Order = apps.get_model('main', 'Order')
    
    # Map Vietnamese display values to English status codes
    status_map = {
        'Đang chờ xử lý': 'PENDING',
        'Đang xử lý': 'PROCESSING',
        'Đã giao cho vận chuyển': 'SHIPPED', 
        'Đã giao hàng': 'DELIVERED',
        'Đã nhận hàng': 'DELIVERED',
        'Đã hủy': 'CANCELLED'
    }
    
    # Fix order statuses
    for order in Order.objects.all():
        # Convert any Vietnamese status values to English codes
        if order.status in status_map:
            order.status = status_map[order.status]
        # Convert lowercase English status codes to uppercase
        elif order.status.upper() in ['PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED']:
            order.status = order.status.upper()
        # Fix default payment_status if it's still PENDING
        if order.payment_status == 'PENDING':
            order.payment_status = 'Đang chờ thanh toán'
        order.save()

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fix_statuses),
    ]