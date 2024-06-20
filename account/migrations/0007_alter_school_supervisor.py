# Generated by Django 5.0.4 on 2024-06-20 10:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_school_supervisor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='school',
            name='supervisor',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='school', to=settings.AUTH_USER_MODEL),
        ),
    ]
