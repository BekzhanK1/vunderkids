# Generated by Django 5.0.4 on 2024-06-19 13:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='supervisor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='school', to=settings.AUTH_USER_MODEL),
        ),
    ]
