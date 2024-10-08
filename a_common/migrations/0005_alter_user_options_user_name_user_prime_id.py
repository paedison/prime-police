# Generated by Django 5.1 on 2024-08-19 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_common', '0004_alter_user_email_alter_user_is_active_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['id'], 'verbose_name': '사용자', 'verbose_name_plural': '사용자'},
        ),
        migrations.AddField(
            model_name='user',
            name='name',
            field=models.CharField(default='', max_length=10, verbose_name='이름'),
        ),
        migrations.AddField(
            model_name='user',
            name='prime_id',
            field=models.CharField(default='', max_length=20, verbose_name='프라임법학원 아이디'),
        ),
    ]
