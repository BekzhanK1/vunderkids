# Generated by Django 4.2.13 on 2024-08-19 15:24

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0002_payment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.IntegerField(validators=[django.core.validators.MaxValueValidator(99999), django.core.validators.MinValueValidator(0)]),
        ),
    ]
