from django.db import models

from .newspapers_model import NewspapersModel
from .publications import Publication


class Issue(NewspapersModel):
    issue_code = models.CharField(max_length=30, default="")
    issue_date = models.DateField()
    input_sub_path = models.CharField(max_length=255, default="")
    publication = models.ForeignKey(
        Publication, on_delete=models.SET_NULL, verbose_name="publication", null=True
    )

    class Meta:
        app_label = "newspapers"
        db_table = "issues"

    def __str__(self):
        return str(self.issue_code)
