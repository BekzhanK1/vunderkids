# Generated by Django 4.2.13 on 2024-07-20 00:02

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0012_alter_user_activation_token_expires_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='activation_token_expires_at',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2024, 7, 21, 0, 2, 7, 70163), null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='reset_password_token_expires_at',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2024, 7, 21, 0, 2, 7, 70180), null=True),
        ),
    ]
