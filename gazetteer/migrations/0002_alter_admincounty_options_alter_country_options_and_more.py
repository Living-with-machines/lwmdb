# Generated by Django 4.2 on 2023-05-04 12:35

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("gazetteer", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="admincounty",
            options={"verbose_name_plural": "admin counties"},
        ),
        migrations.AlterModelOptions(
            name="country",
            options={"verbose_name_plural": "counties"},
        ),
        migrations.AlterModelOptions(
            name="historiccounty",
            options={"verbose_name_plural": "historic counties"},
        ),
    ]