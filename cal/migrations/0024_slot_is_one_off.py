# Generated by Django 4.2.1 on 2023-05-26 23:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cal', '0023_slot_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='slot',
            name='is_one_off',
            field=models.BooleanField(default=False),
        ),
    ]