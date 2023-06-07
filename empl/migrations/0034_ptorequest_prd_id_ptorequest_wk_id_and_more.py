# Generated by Django 4.2.1 on 2023-06-01 04:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('org', '0020_alter_training_sentiment_qual_and_more'),
        ('empl', '0033_alter_daytemplate_cycle_analog_of_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ptorequest',
            name='prd_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='ptorequest',
            name='wk_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='phase_pref',
            field=models.ForeignKey(help_text='The time phase that the employee prefers to work.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='org.timephase'),
        ),
    ]