# Generated by Django 4.2.1 on 2023-05-22 00:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('org', '0006_training_sentiment_qual_training_sentiment_quant'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='image_url',
            field=models.URLField(null=True),
        ),
    ]
