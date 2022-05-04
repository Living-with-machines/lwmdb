from django.db import models

from .newspapers_model import NewspapersModel


class Ingest(NewspapersModel):
    lwm_tool_name = models.CharField(max_length=600, default=None)
    lwm_tool_version = models.CharField(max_length=600, default=None)
    lwm_tool_source = models.CharField(max_length=255, default=None)

    class Meta:
        app_label = "newspapers"
        db_table = "ingests"

    def __str__(self):
        return str(self.lwm_tool_version)
