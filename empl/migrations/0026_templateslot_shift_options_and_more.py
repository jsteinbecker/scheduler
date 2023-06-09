# Generated by Django 4.2.1 on 2023-05-27 23:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('org', '0020_alter_training_sentiment_qual_and_more'),
        ('empl', '0025_employee_pto_hours_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='templateslot',
            name='shift_options',
            field=models.ManyToManyField(blank=True, related_name='generic_template_slots', to='org.shift'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='pto_hours_size',
            field=models.IntegerField(default=10, help_text='The Hour value of a PTO day, this ensures that employees are Scheduled the amount of hours they deserve.'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='template_size',
            field=models.IntegerField(choices=[(2, 'Weeks 2'), (3, 'Weeks 3')], default=2, help_text='Template Size determines the frequency of repetition on assigning a template to schedule.If the employee is to work every other weekend, for example, a 2-week size would be appropriate.'),
        ),
        migrations.AlterField(
            model_name='templateslot',
            name='shift',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='template_slots', to='org.shift'),
        ),
        migrations.CreateModel(
            name='DayOffSlotTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sd_id', models.IntegerField()),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='base_template_slots', to='empl.employee')),
                ('slot_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='base_template_slots', to='empl.templateslotset')),
            ],
            options={
                'ordering': ('sd_id',),
                'abstract': False,
                'unique_together': {('sd_id', 'slot_set')},
            },
        ),
    ]
