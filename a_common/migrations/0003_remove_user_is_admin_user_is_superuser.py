# Generated by Django 5.0.6 on 2024-08-13 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_common', '0002_user_groups_user_user_permissions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_admin',
        ),
        migrations.AddField(
            model_name='user',
            name='is_superuser',
            field=models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status'),
        ),
    ]
