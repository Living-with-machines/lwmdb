import json
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand
from django.db.models import Max
from django.utils import timezone
from tqdm import tqdm

from newspapers.models import DataProvider, Digitisation, Ingest, Issue, Item

from .items import item_cache

LOCAL_STORE: dict[str, dict] = {
    "software": {},
    "ingest": {},
    "data_provider": {},
    "issue": {},
}
current = timezone.now()


def fix_fields(fields):
    """Check correctness of newspapers Item model fields.

    Iterate over the the `digitisation`, `ingest`, `data_provider`,
    `issue`, `ocr_quality_mean` and `ocr_quality_sd` fields, adjusting
    if necessarry. Conclude by updating the `created_at` and
    `updated_at` fields.
    """
    locator_software = fields.get("digitisation__software")
    if not LOCAL_STORE["software"].get(locator_software):
        LOCAL_STORE["software"][locator_software] = Digitisation.objects.get(
            software=locator_software
        ).pk
    del fields["digitisation__software"]

    locator_ingest = (
        fields.get("ingest__lwm_tool_name")
        + "-"
        + fields.get("ingest__lwm_tool_version")
    )
    if not LOCAL_STORE["ingest"].get(locator_ingest):
        LOCAL_STORE["ingest"][locator_ingest] = Ingest.objects.get(
            lwm_tool_name=fields.get("ingest__lwm_tool_name"),
            lwm_tool_version=fields.get("ingest__lwm_tool_version"),
        ).pk
    del fields["ingest__lwm_tool_name"]
    del fields["ingest__lwm_tool_version"]

    locator_dp = fields.get("data_provider")
    if not LOCAL_STORE["data_provider"].get(locator_dp):
        LOCAL_STORE["data_provider"][locator_dp] = DataProvider.objects.get(
            name=fields.get("data_provider")
        ).pk
    del fields["data_provider"]

    locator_issue = fields.get("issue__issue_identifier")
    if not LOCAL_STORE["issue"].get(locator_issue):
        LOCAL_STORE["issue"][locator_issue] = Issue.objects.get(
            issue_code=fields.get("issue__issue_identifier")
        ).pk
    del fields["issue__issue_identifier"]

    fields["digitisation"] = LOCAL_STORE["software"][locator_software]
    fields["ingest"] = LOCAL_STORE["ingest"][locator_ingest]
    fields["data_provider"] = LOCAL_STORE["data_provider"][locator_dp]
    fields["issue"] = LOCAL_STORE["issue"][locator_issue]

    if not fields["ocr_quality_mean"] or fields["ocr_quality_mean"] == "":
        fields["ocr_quality_mean"] = 0

    if not fields["ocr_quality_sd"] or fields["ocr_quality_sd"] == "":
        fields["ocr_quality_sd"] = 0

    fields["created_at"] = str(current)
    fields["updated_at"] = str(current)

    return fields


class Command(BaseCommand):
    help = "Makes Item fixtures from the provided cache folder"

    # def add_arguments(self, parser):
    #     parser.add_argument(
    #         "app",
    #         type=str,
    #         nargs="+",
    #         help="Indicates the app(s) that you want to load fixtures for. You can use 'all' as shorthand for all allowed apps",
    #     )
    #     parser.add_argument(
    #         "-f", "--force", action="store_true", help='Force "yes" on all questions'
    #     )

    def handle(self, *args, **kwargs):
        counter_suggest = Item.objects.all().aggregate(Max("id")).get("id__max") + 1
        _ = input(f"Start counter from current ID ({counter_suggest})? [Y/n]")
        if not _:
            counter = counter_suggest
        else:
            counter = 1

        print(counter)

        for data_provider in ["jisc"]:  # , "hmd", "lwm"]:
            print(data_provider)

            data_provider_dict = {
                "name": data_provider,
                "collection": "newspapers",
                "source_note": "",
            }
            # Get/insert data provider into/from database
            data_provider_o, _ = DataProvider.objects.get_or_create(
                name=data_provider, defaults=data_provider_dict
            )

            path = f"{settings.BASE_DIR}/{item_cache}/{data_provider}/"

            start = datetime.now()
            print()
            print("Started", start)
            text = [x.read_text() for x in Path(path).glob("**/*.jsonl")]
            print("--> File read")
            print(f"[= {round((datetime.now() - start).seconds / 60, 2)} minutes]")

            start = datetime.now()
            print()
            print("Started", start)
            text = [
                json.loads(line)
                for json_lines in tqdm(text, leave=False)
                for line in json_lines.splitlines()
            ]
            print("--> Lines read")
            print(f"[= {round((datetime.now() - start).seconds / 60, 2)} minutes]")

            out_path = f"auto-fixture-{data_provider}.json"

            Path(out_path).unlink() if Path(out_path).exists() else None

            start = datetime.now()
            print()
            print("Started", start)
            d = [
                {"model": "newspapers.Item", "pk": pk, "fields": fix_fields(fields)}
                for pk, fields in enumerate(text, start=counter)
            ]
            print(f"[= {round((datetime.now() - start).seconds / 60, 2)} minutes]")
            # Benchmark: lwm takes about 12-18 min
            # Benchmark: hmd takes about 13-16 min

            Path(out_path).write_text(json.dumps(d))
            self.stdout.write(self.style.SUCCESS(f"Fixture created: {out_path}"))
            self.stdout.write(self.style.NOTICE(f"Now, run in your command line:"))
            self.stdout.write(
                self.style.NOTICE(f"python manage.py loaddata {out_path}")
            )
