from django.db import models
from gazetteer.models import Place, HistoricCounty, AdminCounty


class CensusModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Record(CensusModel):
    REGCNTY_place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        related_name="REGCNTY_census_records",
        related_query_name="REGCNTY_census_record",
    )
    REGCNTY_historic_county = models.ForeignKey(
        HistoricCounty,
        on_delete=models.SET_NULL,
        null=True,
        related_name="REGCNTY_census_records",
        related_query_name="REGCNTY_census_record",
    )
    REGCNTY_admin_county = models.ForeignKey(
        AdminCounty,
        on_delete=models.SET_NULL,
        null=True,
        related_name="REGCNTY_census_records",
        related_query_name="REGCNTY_census_record",
    )

    REGDIST_place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        related_name="REGDIST_census_records",
        related_query_name="REGDIST_census_record",
    )
    REGDIST_historic_county = models.ForeignKey(
        HistoricCounty,
        on_delete=models.SET_NULL,
        null=True,
        related_name="REGDIST_census_records",
        related_query_name="REGDIST_census_record",
    )
    REGDIST_admin_county = models.ForeignKey(
        AdminCounty,
        on_delete=models.SET_NULL,
        null=True,
        related_name="REGDIST_census_records",
        related_query_name="REGDIST_census_record",
    )

    SUBDIST_place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        null=True,
        related_name="SUBDIST_census_records",
        related_query_name="SUBDIST_census_record",
    )
    SUBDIST_historic_county = models.ForeignKey(
        HistoricCounty,
        on_delete=models.SET_NULL,
        null=True,
        related_name="SUBDIST_census_records",
        related_query_name="SUBDIST_census_record",
    )
    SUBDIST_admin_county = models.ForeignKey(
        AdminCounty,
        on_delete=models.SET_NULL,
        null=True,
        related_name="SUBDIST_census_records",
        related_query_name="SUBDIST_census_record",
    )

    CENSUS_YEAR = models.IntegerField()
    CEN = models.IntegerField()

    REGCNTY = models.CharField(max_length=40, blank=False, null=True)
    REGDIST = models.CharField(max_length=40, blank=False, null=True)
    SUBDIST = models.CharField(max_length=40, blank=False, null=True)
    TYPE = models.CharField(max_length=20, blank=False, null=True)

    POP_DENS = models.FloatField(blank=False, null=True)
    POP = models.FloatField(blank=False, null=True)
    ACRES = models.FloatField(blank=False, null=True)
    TFR = models.FloatField(blank=False, null=True)
    ASFR_20_24 = models.FloatField(blank=False, null=True)
    ASFR_25_29 = models.FloatField(blank=False, null=True)
    ASFR_30_34 = models.FloatField(blank=False, null=True)
    ASFR_35_39 = models.FloatField(blank=False, null=True)
    ASFR_40_44 = models.FloatField(blank=False, null=True)
    ASFR_45_49 = models.FloatField(blank=False, null=True)
    TMFR = models.FloatField(blank=False, null=True)
    TMFR_25 = models.FloatField(blank=False, null=True)
    ASMFR_20_24 = models.FloatField(blank=False, null=True)
    ASMFR_25_29 = models.FloatField(blank=False, null=True)
    ASMFR_30_34 = models.FloatField(blank=False, null=True)
    ASMFR_35_39 = models.FloatField(blank=False, null=True)
    ASMFR_40_44 = models.FloatField(blank=False, null=True)
    ASMFR_45_49 = models.FloatField(blank=False, null=True)
    LEGIT_RATE = models.FloatField(blank=False, null=True)
    ILLEG_RATE = models.FloatField(blank=False, null=True)
    ILLEG_RATIO = models.FloatField(blank=False, null=True)
    F_SMAM = models.FloatField(blank=False, null=True)
    M_SMAM = models.FloatField(blank=False, null=True)
    F_CEL_4554 = models.FloatField(blank=False, null=True)
    M_CEL_4554 = models.FloatField(blank=False, null=True)
    IMR = models.FloatField(blank=False, null=True)
    ECMR = models.FloatField(blank=False, null=True)
    DOC = models.FloatField(blank=False, null=True)
    LP_FAM = models.FloatField(blank=False, null=True)
    SINGLE_PER = models.FloatField(blank=False, null=True)
    HOUSE_SERV = models.FloatField(blank=False, null=True)
    BOARD = models.FloatField(blank=False, null=True)
    HH_KIN = models.FloatField(blank=False, null=True)
    AV_AGE = models.FloatField(blank=False, null=True)
    AV_AGE_F = models.FloatField(blank=False, null=True)
    AV_AGE_M = models.FloatField(blank=False, null=True)
    DEPEND = models.FloatField(blank=False, null=True)
    C_WORK_AGE = models.FloatField(blank=False, null=True)
    ELD_WORK_AGE = models.FloatField(blank=False, null=True)
    IRISH_BORN = models.FloatField(blank=False, null=True)
    SR = models.FloatField(blank=False, null=True)
    HC1 = models.FloatField(blank=False, null=True)
    HC2 = models.FloatField(blank=False, null=True)
    HC3 = models.FloatField(blank=False, null=True)
    HC4 = models.FloatField(blank=False, null=True)
    HC5 = models.FloatField(blank=False, null=True)
    SC1 = models.FloatField(blank=False, null=True)
    SC2 = models.FloatField(blank=False, null=True)
    SC3 = models.FloatField(blank=False, null=True)
    SC4 = models.FloatField(blank=False, null=True)
    SC5 = models.FloatField(blank=False, null=True)
    SC6 = models.FloatField(blank=False, null=True)
    SC7 = models.FloatField(blank=False, null=True)
    SC8 = models.FloatField(blank=False, null=True)
    FMAR_PRATE = models.FloatField(blank=False, null=True)
    FNM_PRATE = models.FloatField(blank=False, null=True)
    FWID_PRATE = models.FloatField(blank=False, null=True)
    F_DOM = models.FloatField(blank=False, null=True)
    F_TEX = models.FloatField(blank=False, null=True)
    C_TEACHER = models.FloatField(blank=False, null=True)
    F_CL_1013 = models.FloatField(blank=False, null=True)
    M_CL_1013 = models.FloatField(blank=False, null=True)
    F_CL_1418 = models.FloatField(blank=False, null=True)
    M_CL_1418 = models.FloatField(blank=False, null=True)

    def __str__(self):
        return f"{self.CEN} ({self.CENSUS_YEAR})"
