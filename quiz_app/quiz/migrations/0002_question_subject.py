# Generated by Django 5.1.6 on 2025-02-16 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='subject',
            field=models.CharField(default='unknown', max_length=255),
            preserve_default=False,
        ),
    ]
