# Generated by Django 3.2.12 on 2022-05-03 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('press_directories', '0008_null_true_Json'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mitchells',
            name='price_raw',
            field=models.JSONField(null=True),
        ),
    ]
