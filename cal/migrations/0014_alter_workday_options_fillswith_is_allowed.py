# Generated by Django 4.2.1 on 2023-05-24 05:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cal', '0013_slot_conflicting_slots'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='workday',
            options={'ordering': ['date', 'version__num']},
        ),
        migrations.AddField(
            model_name='fillswith',
            name='is_allowed',
            field=models.BooleanField(default=True),
        ),
    ]