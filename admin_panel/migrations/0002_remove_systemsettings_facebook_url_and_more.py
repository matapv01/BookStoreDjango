# Generated by Django 5.1.7 on 2025-05-20 20:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='systemsettings',
            name='facebook_url',
        ),
        migrations.RemoveField(
            model_name='systemsettings',
            name='instagram_url',
        ),
        migrations.RemoveField(
            model_name='systemsettings',
            name='site_logo',
        ),
        migrations.RemoveField(
            model_name='systemsettings',
            name='twitter_url',
        ),
    ]
