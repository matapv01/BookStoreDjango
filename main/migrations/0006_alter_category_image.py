# Generated by Django 5.1.7 on 2025-05-20 21:27

import cloudinary_storage.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_category_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='image',
            field=models.ImageField(blank=True, help_text='Hình ảnh danh mục', null=True, storage=cloudinary_storage.storage.MediaCloudinaryStorage(), upload_to='categories/'),
        ),
    ]
