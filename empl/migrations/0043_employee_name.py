# Generated by Django 4.2.1 on 2023-06-04 22:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empl', '0042_daytemplateset_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='name',
            field=models.CharField(max_length=128, null=True),
        ),
    ]