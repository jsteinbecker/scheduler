# Generated by Django 4.2.1 on 2023-06-01 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cal', '0038_alter_fillswith_options_and_more'),
        ('empl', '0035_employee_std_slot_size_employeeweekmonitor_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='templateddayoffset',
            name='employee',
        ),
        migrations.RemoveField(
            model_name='daytemplateset',
            name='active',
        ),
        migrations.AddField(
            model_name='daytemplateset',
            name='expiration_date',
            field=models.DateField(null=True),
        ),
        migrations.DeleteModel(
            name='TemplatedDayOff',
        ),
        migrations.DeleteModel(
            name='TemplatedDayOffSet',
        ),
    ]
