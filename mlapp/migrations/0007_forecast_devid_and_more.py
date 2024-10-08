# Generated by Django 4.2.11 on 2024-06-19 09:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mlapp', '0006_alter_correlation_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='forecast',
            name='devId',
            field=models.CharField(default='devId', max_length=50),
        ),
        migrations.AlterField(
            model_name='correlationmonth',
            name='calculation_timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 6, 19, 9, 45, 24, 841331, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='correlationtoday',
            name='calculation_timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 6, 19, 9, 45, 24, 841331, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='forecast',
            name='timestamp',
            field=models.DateTimeField(default=datetime.date(2024, 6, 19)),
        ),
    ]
