# Generated by Django 4.2.1 on 2023-05-27 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cal', '0028_fillswith_is_assigned'),
    ]

    operations = [
        migrations.AddField(
            model_name='version',
            name='n_empty',
            field=models.IntegerField(default=0),
        ),
    ]
