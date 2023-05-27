# Generated by Django 4.2.1 on 2023-05-26 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cal', '0022_schedule_pto_list'),
    ]

    operations = [
        migrations.AddField(
            model_name='slot',
            name='state',
            field=models.CharField(choices=[('N', 'Normal'), ('T', 'Turnaround'), ('O', 'Overtime')], default='N', max_length=1),
        ),
    ]