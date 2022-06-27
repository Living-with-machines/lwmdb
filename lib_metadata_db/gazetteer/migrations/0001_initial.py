# Generated by Django 3.2.13 on 2022-06-27 15:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdminCounty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('admin_county_label', models.CharField(default=None, max_length=255)),
                ('admin_county_wikidata_id', models.CharField(default=None, max_length=30)),
            ],
            options={
                'db_table': 'admin_county',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('country_label', models.CharField(default=None, max_length=255)),
                ('country_wikidata_id', models.CharField(default=None, max_length=30)),
            ],
            options={
                'db_table': 'country',
            },
        ),
        migrations.CreateModel(
            name='HistoricCounty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('hcounty_label', models.CharField(default=None, max_length=255)),
                ('hcounty_wikidata_id', models.CharField(default=None, max_length=30)),
            ],
            options={
                'db_table': 'historic_county',
            },
        ),
        migrations.CreateModel(
            name='PlaceOfPublication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('place_wikidata_id', models.CharField(default=None, max_length=30)),
                ('place_label', models.CharField(default=None, max_length=255)),
                ('latitude', models.FloatField(null=True)),
                ('longitude', models.FloatField(null=True)),
                ('geonames_ids', models.CharField(default=None, max_length=255)),
                ('admin_county', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='gazetteer.admincounty', verbose_name='admin_county')),
                ('country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='gazetteer.country', verbose_name='county')),
                ('historic_county', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='gazetteer.historiccounty', verbose_name='historic_county')),
            ],
            options={
                'db_table': 'place_of_publication',
            },
        ),
    ]
