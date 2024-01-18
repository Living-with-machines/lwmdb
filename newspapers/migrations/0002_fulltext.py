# Generated by Django 4.2.7 on 2024-01-17 11:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("newspapers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FullText",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("text", models.TextField()),
                ("item_code", models.CharField(blank=True, max_length=600, null=True)),
                ("text_path", models.CharField(blank=True, max_length=1000, null=True)),
                (
                    "text_compressed_path",
                    models.CharField(blank=True, max_length=1000, null=True),
                ),
                (
                    "text_fixture_path",
                    models.CharField(blank=True, max_length=1000, null=True),
                ),
                ("errors", models.TextField(blank=True, null=True)),
                ("info", models.TextField(blank=True, null=True)),
                ("canonical", models.BooleanField(default=False)),
                (
                    "item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="full_texts",
                        related_query_name="full_text",
                        to="newspapers.item",
                        verbose_name="Full Text",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
