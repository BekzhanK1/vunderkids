# Generated by Django 5.0.4 on 2024-05-10 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0015_child_league_child_xp_student_league_student_xp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]