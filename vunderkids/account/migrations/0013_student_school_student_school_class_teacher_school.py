# Generated by Django 5.0.3 on 2024-03-17 09:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0012_alter_child_grade'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='students', to='account.school'),
        ),
        migrations.AddField(
            model_name='student',
            name='school_class',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students', to='account.class'),
        ),
        migrations.AddField(
            model_name='teacher',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='teachers', to='account.school'),
        ),
    ]