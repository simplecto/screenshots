# Generated by Django 3.0.3 on 2020-03-21 18:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shots', '0021_screenshot_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='screenshot',
            name='image_binary',
        ),
    ]
