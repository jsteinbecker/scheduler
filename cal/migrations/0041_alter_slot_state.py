# Generated by Django 4.2.1 on 2023-06-02 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cal', '0040_alter_slot_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slot',
            name='state',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]