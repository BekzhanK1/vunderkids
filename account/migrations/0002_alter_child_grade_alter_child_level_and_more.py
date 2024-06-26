# Generated by Django 5.0.4 on 2024-06-09 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='child',
            name='grade',
            field=models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10'), (11, '11'), (12, '12')], db_index=True),
        ),
        migrations.AlterField(
            model_name='child',
            name='level',
            field=models.PositiveIntegerField(db_index=True, default=1),
        ),
        migrations.AlterField(
            model_name='student',
            name='grade',
            field=models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10'), (11, '11'), (12, '12')], db_index=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='level',
            field=models.PositiveIntegerField(db_index=True, default=1),
        ),
    ]
