import json
import re
from pathlib import Path

import pandas as pd
from django.utils import timezone
from tqdm import tqdm

from gazetteer.models import AdminCounty, HistoricCounty, Place

from .fixtures import Fixture

CSV_FIXTURE_PATH: Path = Path("./fixture-files/UKDA-8613-csv/")
JSON_FIXTURE_WRITE_PATH: Path = Path("./census/fixtures/Record.json")


class CensusFixture(Fixture):
    """Build census."""

    csv_fixture_path: Path = CSV_FIXTURE_PATH
    json_fixture_write_path: Path = JSON_FIXTURE_WRITE_PATH

    def __init__(self, force=False):
        self.force = force
        super(Fixture, self).__init__()

    def build_fixture(self):
        CSV_FILES = [x for x in self.csv_fixture_path.glob("*.csv")]

        df = pd.DataFrame()
        now = timezone.now()

        for file in (bar1 := tqdm(CSV_FILES, leave=False)):
            bar1.set_description(file.name)

            year, *_ = re.findall(r"\d{4}", str(file.name))
            _df = pd.read_csv(file)
            _df = _df.rename({f"CEN_{year}": "CEN"}, axis=1)
            _df["CENSUS_YEAR"] = year
            _df = _df[
                ["CENSUS_YEAR"] + [x for x in _df.columns if not x == "CENSUS_YEAR"]
            ]

            df = pd.concat([df, _df])

        df = df.rename(
            {col: col.replace("-", "_") for col in df.columns if "-" in col},
            axis=1,
        )
        df = df.reset_index(drop=True)
        df["pk"] = df.index + 1
        df["created_at"] = str(now)
        df["updated_at"] = str(now)

        def get_rel(x):
            # do some manual data wrangling - on hold until Mariona is back
            if "yorkshire" in x.lower():
                x = "YORKSHIRE"

            if "bury" in x and "edmund" in x.lower():
                x = "Bury St Edmunds"

            ##### first try
            try:
                historic_county = HistoricCounty.objects.get(label__iexact=x).pk
            except:
                historic_county = None

            try:
                admin_county = AdminCounty.objects.get(label__iexact=x).pk
            except:
                admin_county = None

            try:
                place = Place.objects.get(label__iexact=x).pk
            except:
                place = None

            if historic_county != None or admin_county != None or place != None:
                return (x, historic_county, admin_county, place)

            ##### second try: without EAST/WEST/NORTH/SOUTH/WESTERN/SOUTHEAST/FIRST/CENTRAL
            if historic_county == None and place == None:
                for word in [
                    "east",
                    "north",
                    "west",
                    "south",
                    "western",
                    "southeast",
                    "first",
                    "central",
                    "south east",
                ]:
                    if f"{word} " in x.lower() or f" {word}" in x.lower():
                        x = x.replace(f"{word} ", " ").replace(f" {word}", " ").strip()
                        x = (
                            x.replace(f"{word.upper()} ", " ")
                            .replace(f" {word.upper()}", " ")
                            .strip()
                        )

            try:
                historic_county = HistoricCounty.objects.get(label__iexact=x).pk
            except:
                historic_county = None

            try:
                admin_county = AdminCounty.objects.get(label__iexact=x).pk
            except:
                admin_county = None

            try:
                place = Place.objects.get(label__iexact=x).pk
            except:
                place = None

            return (x, historic_county, admin_county, place)

        cats = ["REGCNTY", "REGDIST", "SUBDIST"]

        for cat in (bar1 := tqdm(cats, leave=False)):
            bar1.set_description(f"Correcting record :: {cat}")
            df[f"{cat}_rel"] = df[cat].apply(lambda x: get_rel(x))
            df[f"{cat}_historic_county_id"] = df[f"{cat}_rel"].apply(lambda x: x[1])
            df[f"{cat}_admin_county_id"] = df[f"{cat}_rel"].apply(lambda x: x[2])
            df[f"{cat}_place_id"] = df[f"{cat}_rel"].apply(lambda x: x[3])

        df.drop([f"{cat}_rel" for cat in cats], axis=1, inplace=True)

        lst = []
        for record in json.loads(df.to_json(orient="records")):
            pk = record.pop("pk")
            lst.append({"model": "census.Record", "pk": pk, "fields": record})

        self.json_fixture_write_path.write_text(json.dumps(lst))

        self.stdout.write(
            self.style.SUCCESS("Fixture file written. Now run the following command:")
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"python manage.py loaddata {self.json_fixture_write_path}"
            )
        )
