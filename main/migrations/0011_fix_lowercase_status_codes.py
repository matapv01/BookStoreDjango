from django.db import migrations

def fix_lowercase_status_codes(apps, schema_editor):
    Order = apps.get_model('main', 'Order')
    
    # Fix order statuses
    for order in Order.objects.all():
        # Convert lowercase English status codes to uppercase
        if order.status.upper() in ['PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED'] and order.status != order.status.upper():
            order.status = order.status.upper()
            order.save()

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_fix_payment_and_order_statuses'),
    ]

    operations = [
        migrations.RunPython(fix_lowercase_status_codes),
    ]