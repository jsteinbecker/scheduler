# Generated by Django 4.2.1 on 2023-05-27 23:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('org', '0019_shift_on_holidays'),
    ]

    operations = [
        migrations.AlterField(
            model_name='training',
            name='sentiment_qual',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Strongly Dislike'), (2, 'Dislike'), (3, 'Neutral'), (4, 'Prefer'), (5, 'Strongly Prefer')], default=3, help_text="The 'in general' value for how the employee feels about this shift, regardless of how they feel about other shifts."),
        ),
        migrations.AlterField(
            model_name='training',
            name='sentiment_quant',
            field=models.PositiveSmallIntegerField(default=0, help_text="The 'in comparison' value for how the employee feels about this shift, asking them to rank this shift against other shifts."),
        ),
    ]
