# Generated by Django 4.2.13 on 2024-08-19 21:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0005_alter_plan_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='invoice_id_alt',
            field=models.CharField(default='82828282', max_length=15, unique=True),
            preserve_default=False,
        ),
    ]