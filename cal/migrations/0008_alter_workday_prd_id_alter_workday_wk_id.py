# Generated by Django 4.2.1 on 2023-05-22 00:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cal', '0007_workday_prd_id_workday_wk_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workday',
            name='prd_id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='workday',
            name='wk_id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
