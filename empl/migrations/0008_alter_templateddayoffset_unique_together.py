# Generated by Django 4.2.1 on 2023-05-23 22:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('empl', '0007_alter_templateddayoff_tdo_set'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='templateddayoffset',
            unique_together={('employee', 'active')},
        ),
    ]