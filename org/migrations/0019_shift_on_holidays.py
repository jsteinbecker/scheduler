# Generated by Django 4.2.1 on 2023-05-27 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('org', '0018_alter_training_options_alter_training_sentiment_qual_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='on_holidays',
            field=models.BooleanField(default=True),
        ),
    ]
