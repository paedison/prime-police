# Generated by Django 5.1 on 2024-09-23 08:10

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_daily', '0002_alter_exam_unique_together_exam_unique_daily_exam'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='opened_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='공개일시'),
        ),
    ]
