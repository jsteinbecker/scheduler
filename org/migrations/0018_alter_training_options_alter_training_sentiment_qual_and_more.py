# Generated by Django 4.2.1 on 2023-05-27 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('org', '0017_alter_departmentnotification_message'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='training',
            options={'ordering': ('sentiment_quant', 'sentiment_qual')},
        ),
        migrations.AlterField(
            model_name='training',
            name='sentiment_qual',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Strongly Dislike'), (2, 'Dislike'), (3, 'Neutral'), (4, 'Prefer'), (5, 'Strongly Prefer')], default=3),
        ),
        migrations.AlterField(
            model_name='training',
            name='sentiment_quant',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
