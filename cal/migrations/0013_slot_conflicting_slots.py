# Generated by Django 4.2.1 on 2023-05-24 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cal', '0012_fillswith_exceeds_period_fte_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='slot',
            name='conflicting_slots',
            field=models.ManyToManyField(blank=True, related_name='conflicts', to='cal.slot'),
        ),
    ]
