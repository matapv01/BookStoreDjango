# Generated by Django 5.1.7 on 2025-05-20 21:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_change_product_image_to_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='image',
            field=models.URLField(blank=True, help_text='URL của hình ảnh danh mục trên Cloudinary', max_length=500, null=True),
        ),
    ]
