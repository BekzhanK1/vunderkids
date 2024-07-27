# Generated by Django 4.2.13 on 2024-07-24 21:00

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_alter_user_activation_token_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='activation_token_expires_at',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2024, 7, 25, 21, 0, 59, 418751, tzinfo=datetime.timezone.utc), null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='reset_password_token_expires_at',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2024, 7, 25, 21, 0, 59, 418785, tzinfo=datetime.timezone.utc), null=True),
        ),
    ]