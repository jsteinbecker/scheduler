# Generated by Django 4.2.1 on 2023-06-01 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('org', '0021_alter_timephase_position'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='department',
            name='template_week_count_full_time',
        ),
        migrations.RemoveField(
            model_name='department',
            name='template_week_count_part_time',
        ),
        migrations.AlterField(
            model_name='timephase',
            name='position',
            field=models.PositiveSmallIntegerField(null=True),
        ),
    ]
