# Generated by Django 4.2.1 on 2023-05-29 07:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('empl', '0033_alter_daytemplate_cycle_analog_of_and_more'),
        ('cal', '0030_alter_slot_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slot',
            name='state',
            field=models.CharField(choices=[('E', 'Empty'), ('N', 'Normal'), ('T', 'Turnaround'), ('O', 'Overtime'), ('P', 'PTO Conflict'), ('D', 'TDO Conflict'), ('1', 'One Off')], default='E', max_length=1),
        ),
        migrations.CreateModel(
            name='WeekSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week', models.IntegerField()),
                ('hours', models.IntegerField(default=0)),
                ('goal_hours', models.IntegerField(default=0)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='week_summaries', to='empl.employee')),
                ('version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='week_summaries', to='cal.version')),
            ],
            options={
                'verbose_name_plural': 'Week Summaries',
                'ordering': ('employee', '-hours'),
                'unique_together': {('version', 'employee', 'week')},
            },
        ),
    ]
