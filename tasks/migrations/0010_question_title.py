# Generated by Django 5.0.4 on 2024-06-11 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0009_taskcompletion_correct'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='title',
            field=models.CharField(default='Default Title', max_length=100),
            preserve_default=False,
        ),
    ]
