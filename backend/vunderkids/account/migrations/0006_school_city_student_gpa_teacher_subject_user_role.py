# Generated by Django 5.0.3 on 2024-03-16 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_remove_user_role_parent_alter_child_parent_school_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='city',
            field=models.CharField(default='Astana', max_length=150),
        ),
        migrations.AddField(
            model_name='student',
            name='gpa',
            field=models.SmallIntegerField(blank=True, default=4, null=True),
        ),
        migrations.AddField(
            model_name='teacher',
            name='subject',
            field=models.CharField(default='Astana', max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(blank=True, choices=[('school', 'School'), ('teacher', 'Teacher'), ('student', 'Student'), ('parent', 'Parent'), ('principal', 'Principal'), ('admin', 'Admin')], max_length=15, null=True),
        ),
    ]
