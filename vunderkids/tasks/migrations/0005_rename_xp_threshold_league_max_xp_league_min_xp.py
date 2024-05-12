# Generated by Django 5.0.4 on 2024-05-07 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_task_data_taskresponse_delete_taskcompletion'),
    ]

    operations = [
        migrations.RenameField(
            model_name='league',
            old_name='xp_threshold',
            new_name='max_xp',
        ),
        migrations.AddField(
            model_name='league',
            name='min_xp',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
    ]