# Generated by Django 5.1.7 on 2025-05-21 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0003_alter_systemsettings_is_active_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='systemsettings',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Khi tắt, website sẽ tự động chuyển sang chế độ bảo trì'),
        ),
    ]
