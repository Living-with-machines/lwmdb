# Generated by Django 3.2.13 on 2022-08-18 15:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gazetteer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Record',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('CENSUS_YEAR', models.IntegerField()),
                ('CEN', models.IntegerField()),
                ('REGCNTY', models.CharField(max_length=40, null=True)),
                ('REGDIST', models.CharField(max_length=40, null=True)),
                ('SUBDIST', models.CharField(max_length=40, null=True)),
                ('TYPE', models.CharField(max_length=20, null=True)),
                ('POP_DENS', models.FloatField(null=True)),
                ('POP', models.FloatField(null=True)),
                ('ACRES', models.FloatField(null=True)),
                ('TFR', models.FloatField(null=True)),
                ('ASFR_20_24', models.FloatField(null=True)),
                ('ASFR_25_29', models.FloatField(null=True)),
                ('ASFR_30_34', models.FloatField(null=True)),
                ('ASFR_35_39', models.FloatField(null=True)),
                ('ASFR_40_44', models.FloatField(null=True)),
                ('ASFR_45_49', models.FloatField(null=True)),
                ('TMFR', models.FloatField(null=True)),
                ('TMFR_25', models.FloatField(null=True)),
                ('ASMFR_20_24', models.FloatField(null=True)),
                ('ASMFR_25_29', models.FloatField(null=True)),
                ('ASMFR_30_34', models.FloatField(null=True)),
                ('ASMFR_35_39', models.FloatField(null=True)),
                ('ASMFR_40_44', models.FloatField(null=True)),
                ('ASMFR_45_49', models.FloatField(null=True)),
                ('LEGIT_RATE', models.FloatField(null=True)),
                ('ILLEG_RATE', models.FloatField(null=True)),
                ('ILLEG_RATIO', models.FloatField(null=True)),
                ('F_SMAM', models.FloatField(null=True)),
                ('M_SMAM', models.FloatField(null=True)),
                ('F_CEL_4554', models.FloatField(null=True)),
                ('M_CEL_4554', models.FloatField(null=True)),
                ('IMR', models.FloatField(null=True)),
                ('ECMR', models.FloatField(null=True)),
                ('DOC', models.FloatField(null=True)),
                ('LP_FAM', models.FloatField(null=True)),
                ('SINGLE_PER', models.FloatField(null=True)),
                ('HOUSE_SERV', models.FloatField(null=True)),
                ('BOARD', models.FloatField(null=True)),
                ('HH_KIN', models.FloatField(null=True)),
                ('AV_AGE', models.FloatField(null=True)),
                ('AV_AGE_F', models.FloatField(null=True)),
                ('AV_AGE_M', models.FloatField(null=True)),
                ('DEPEND', models.FloatField(null=True)),
                ('C_WORK_AGE', models.FloatField(null=True)),
                ('ELD_WORK_AGE', models.FloatField(null=True)),
                ('IRISH_BORN', models.FloatField(null=True)),
                ('SR', models.FloatField(null=True)),
                ('HC1', models.FloatField(null=True)),
                ('HC2', models.FloatField(null=True)),
                ('HC3', models.FloatField(null=True)),
                ('HC4', models.FloatField(null=True)),
                ('HC5', models.FloatField(null=True)),
                ('SC1', models.FloatField(null=True)),
                ('SC2', models.FloatField(null=True)),
                ('SC3', models.FloatField(null=True)),
                ('SC4', models.FloatField(null=True)),
                ('SC5', models.FloatField(null=True)),
                ('SC6', models.FloatField(null=True)),
                ('SC7', models.FloatField(null=True)),
                ('SC8', models.FloatField(null=True)),
                ('FMAR_PRATE', models.FloatField(null=True)),
                ('FNM_PRATE', models.FloatField(null=True)),
                ('FWID_PRATE', models.FloatField(null=True)),
                ('F_DOM', models.FloatField(null=True)),
                ('F_TEX', models.FloatField(null=True)),
                ('C_TEACHER', models.FloatField(null=True)),
                ('F_CL_1013', models.FloatField(null=True)),
                ('M_CL_1013', models.FloatField(null=True)),
                ('F_CL_1418', models.FloatField(null=True)),
                ('M_CL_1418', models.FloatField(null=True)),
                ('REGCNTY_admin_county', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='REGCNTY_census_records', related_query_name='REGCNTY_census_record', to='gazetteer.admincounty')),
                ('REGCNTY_historic_county', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='REGCNTY_census_records', related_query_name='REGCNTY_census_record', to='gazetteer.historiccounty')),
                ('REGCNTY_place', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='REGCNTY_census_records', related_query_name='REGCNTY_census_record', to='gazetteer.place')),
                ('REGDIST_admin_county', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='REGDIST_census_records', related_query_name='REGDIST_census_record', to='gazetteer.admincounty')),
                ('REGDIST_historic_county', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='REGDIST_census_records', related_query_name='REGDIST_census_record', to='gazetteer.historiccounty')),
                ('REGDIST_place', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='REGDIST_census_records', related_query_name='REGDIST_census_record', to='gazetteer.place')),
                ('SUBDIST_admin_county', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='SUBDIST_census_records', related_query_name='SUBDIST_census_record', to='gazetteer.admincounty')),
                ('SUBDIST_historic_county', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='SUBDIST_census_records', related_query_name='SUBDIST_census_record', to='gazetteer.historiccounty')),
                ('SUBDIST_place', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='SUBDIST_census_records', related_query_name='SUBDIST_census_record', to='gazetteer.place')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
