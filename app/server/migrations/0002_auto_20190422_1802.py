# Generated by Django 2.1.7 on 2019-04-22 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='end_offset',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='document',
            name='parent_document',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='document',
            name='start_offset',
            field=models.IntegerField(default=-1),
        ),
    ]
