# Generated by Django 4.1.7 on 2023-02-23 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newspapers', '0003_alter_item_fulltext'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='title_char_count',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='item',
            name='title_truncated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='item',
            name='title_word_count',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='item',
            name='word_char_count',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='title',
            field=models.CharField(default=None, max_length=280),
        ),
    ]
