# Generated by Django 5.0.4 on 2024-06-11 17:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0008_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskcompletion',
            name='correct',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
