# Generated by Django 4.2.1 on 2023-05-21 02:59

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empl', '0002_employee_linked_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='hire_date',
            field=models.DateField(default=datetime.date(2018, 4, 11)),
        ),
        migrations.AddField(
            model_name='employee',
            name='time_pref',
            field=models.CharField(choices=[('AM', 'MORNING'), ('PM', 'EVENING'), ('XN', 'OVERNIGHT')], default='AM', max_length=4),
        ),
    ]
