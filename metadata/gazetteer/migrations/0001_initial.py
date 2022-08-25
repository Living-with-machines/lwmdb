# Generated by Django 3.2.13 on 2022-08-18 15:02

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
                ('label', models.CharField(default=None, max_length=255)),
                ('wikidata_id', models.CharField(default=None, max_length=30)),
            ],
            options={
                'unique_together': {('wikidata_id', 'label')},
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('label', models.CharField(default=None, max_length=255)),
                ('wikidata_id', models.CharField(default=None, max_length=30)),
            ],
            options={
                'unique_together': {('wikidata_id', 'label')},
            },
        ),
        migrations.CreateModel(
            name='HistoricCounty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('label', models.CharField(default=None, max_length=255)),
                ('wikidata_id', models.CharField(default=None, max_length=30)),
            ],
            options={
                'unique_together': {('wikidata_id', 'label')},
            },
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('wikidata_id', models.CharField(default=None, max_length=30)),
                ('label', models.CharField(default=None, max_length=255)),
                ('latitude', models.FloatField(null=True)),
                ('longitude', models.FloatField(null=True)),
                ('geonames_ids', models.CharField(default=None, max_length=255, null=True)),
                ('admin_county', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='places', related_query_name='place', to='gazetteer.admincounty', verbose_name='admin_county')),
                ('country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='places', related_query_name='place', to='gazetteer.country', verbose_name='country')),
                ('historic_county', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='places', related_query_name='place', to='gazetteer.historiccounty', verbose_name='historic_county')),
            ],
            options={
                'unique_together': {('wikidata_id', 'label')},
            },
        ),
    ]