# Generated by Django 4.2.1 on 2023-05-26 06:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empl', '0018_remove_employee_time_pref_employee_phase_pref'),
        ('cal', '0021_fillswith_has_pto_fillswith_has_tdo'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='pto_list',
            field=models.ManyToManyField(related_name='schedules', to='empl.ptorequest'),
        ),
    ]