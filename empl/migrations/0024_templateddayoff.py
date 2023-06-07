# Generated by Django 4.2.1 on 2023-05-27 18:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('empl', '0023_employee_trade_one_offs'),
    ]

    operations = [
        migrations.CreateModel(
            name='TemplatedDayOff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('effective_date', models.DateField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('day_id', models.IntegerField()),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='templated_days_off', to='empl.employee')),
            ],
            options={
                'unique_together': {('employee', 'day_id', 'active')},
            },
        ),
    ]