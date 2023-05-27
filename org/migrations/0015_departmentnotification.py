# Generated by Django 4.2.1 on 2023-05-25 15:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('org', '0014_alter_timephase_position'),
    ]

    operations = [
        migrations.CreateModel(
            name='DepartmentNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('info', 'info'), ('warning', 'warning'), ('error', 'error')], max_length=64)),
                ('message', models.CharField(max_length=256)),
                ('date', models.DateField(auto_now_add=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='org.department')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]