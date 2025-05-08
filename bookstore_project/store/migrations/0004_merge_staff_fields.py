from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('store', '0002_add_staff_fields'),
        ('store', '0003_users_last_login_alter_users_password'),
    ]

    operations = [
        # Empty operations since both migrations already define their changes
    ]
