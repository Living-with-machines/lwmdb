from django.core.management import BaseCommand
from django.conf import settings
from pathlib import Path
from django.core.serializers import serialize, deserialize
from django.db.utils import OperationalError
from django.utils import timezone
import pandas as pd
import json
from mitchells.models import Entry
from newspapers.models import Newspaper
from gazetteer.models import Place

# where to find the most important files to build the fixtures
AUTO_FILE_LOCATIONS = {
    "wikidata_gazetteer": "fixture-files/wikidata_gazetteer_selected.csv",
    "dict_admin_counties": "fixture-files/dict_admin_counties.json",
    "dict_historic_counties": "fixture-files/dict_historic_counties.json",
    "dict_countries": "fixture-files/dict_countries.json",
    "wikidata_ids_publication_mitchells": "fixture-files/wikidata_ids_publication_mitchells.txt",
    "mitchells_db": "fixture-files/mitchells_db.csv",
    "newspapers_overview": "fixture-files/newspapers_overview_with_links.csv",
    "mitchells_publication_for_linking": "fixture-files/mitchells_publication_for_linking.csv",
    "nlp_loc_wikidata_concat": "fixture-files/nlp_loc_wikidata_concat.csv",
}

# "lwm", "hmd", "jisc", "bna"]  # which are our data providers
DATA_PROVIDERS = ["jisc"]
MOUNTPOINT = "cache-alto2txt/{data_provider}-alto2txt/metadata/"  # where the alto2txt metadata is mounted for each provider (or local copies stored)

# automatically map the correct data provider to each mountpoint string for ease of access later
MOUNTPOINTS = {
    x: MOUNTPOINT.format_map({"data_provider": y for y in DATA_PROVIDERS if y == x})
    for x in DATA_PROVIDERS
}


class Fixture(BaseCommand):
    def write_models(self, models):
        lst = []
        df = None

        for x in models:
            try:
                df, model = x
            except TypeError:
                try:
                    model = x
                except Exception as e:
                    exit(f"An exception occurred: {e}")

            filename = f"{model._meta.label.split('.')[-1]}-fixtures.json"
            operational_errors_occurred = 0

            if isinstance(df, pd.DataFrame):
                df_json = df.to_json(orient="index")

                for pk, fields in json.loads(df_json).items():
                    try:
                        model.objects.update_or_create(id=pk, defaults=fields)
                    except OperationalError:
                        operational_errors_occurred += 1

            if operational_errors_occurred:
                self.stdout.write(
                    self.style.WARNING(
                        f"{operational_errors_occurred} operational error(s) occurred: rows not written to database."
                    )
                )

            path = self.get_output_dir() / filename

            model_fields = model._meta.get_fields()
            data = serialize(
                "json",
                model.objects.all(),
                fields=[
                    x.name
                    for x in model_fields
                    if not x.name in ["created_at", "updated_at"]
                ],
            )

            with open(path, "w+") as f:
                f.write(data)

        return True

    def load_fixtures(self, models=None):
        if not models:
            models = self.models

        for model in models:
            success = 0
            path = (
                self.get_output_dir()
                / f"{model._meta.label.split('.')[-1]}-fixtures.json"
            )

            if not Path(path).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Warning: Model {model._meta.label} is missing a fixture file and will not load."
                    )
                )
                continue

            data = path.read_text()
            for obj in deserialize("json", data):
                value = timezone.now()
                setattr(obj.object, "created_at", value)
                setattr(obj.object, "updated_at", value)
                obj.save()
                success += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Wrote {success} objects of model {obj.object._meta.model._meta.label} to db"
                )
            )

    def get_output_dir(self, app_name=None):
        if app_name:
            return settings.BASE_DIR / Path(f"{app_name}/fixtures")
        return settings.BASE_DIR / Path(f"{self.app_name}/fixtures")

    def get_input(self, msg, suggestion):
        self.stdout.write(
            self.style.NOTICE(f"{msg}\n[{settings.BASE_DIR / suggestion}]")
        )
        _ = input()

        if _:
            return _

        return suggestion

    def try_file(self, path, return_contents=True, func=False, relative_to_django=True):
        if relative_to_django:
            path = settings.BASE_DIR / path

        if not Path(path).exists():
            self.stdout.write(self.style.ERROR(f"File does not exist: {path}"))
            exit()

        if return_contents:
            if func:
                return func(Path(path).read_text())

            return Path(path).read_text()

        return Path(path)

    def done(self):
        self.stdout.write(self.style.SUCCESS(f"{self.app_name}: Done"))


class Connector(Fixture):
    def __init__(self, force=False):
        self.force = force
        super(Fixture, self).__init__()

    def special_write_fixture(self):
        # Save all Newspaper
        model = Newspaper
        filename = f"{model._meta.label.split('.')[-1]}-fixtures.json"
        model_fields = model._meta.get_fields()
        path = self.get_output_dir("newspapers") / filename
        data = serialize(
            "json",
            model.objects.all(),
            fields=[
                x.name
                for x in model_fields
                if not x.name in ["created_at", "updated_at"]
            ],
        )
        with open(path, "w+") as f:
            f.write(data)

    def connect(self):
        # Now we want to attempt to connect mitchells.Entry > newspapers.Newspaper
        mitchells_publication_for_linking = (
            self.get_input(
                "Where is mitchells_publication_for_linking.csv?",
                AUTO_FILE_LOCATIONS["mitchells_publication_for_linking"],
            )
            if not self.force
            else AUTO_FILE_LOCATIONS["mitchells_publication_for_linking"]
        )
        self.try_file(mitchells_publication_for_linking, False)

        df = pd.read_csv(mitchells_publication_for_linking, dtype={"NLP": str})

        for _, row in df.iterrows():
            if not Newspaper.objects.filter(publication_code=row.NLP):
                self.stdout.write(
                    self.style.WARNING(
                        f"NLP {row.NLP} not found in database => failed connection to mitchells.Publication {row.entry}."
                    )
                )
                continue

            entry = Entry.objects.get(pk=row.entry)
            for newspaper in Newspaper.objects.filter(publication_code=row.NLP):
                entry.newspaper = newspaper
                entry.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"NLP {row.NLP} connected to mitchells.Entry {row.entry}."
                    )
                )

        self.special_write_fixture()

        # Now we want to attempt to connect newspapers.Newspaper > gazetteer.Place
        nlp_loc_wikidata_concat = (
            self.get_input(
                "Where is nlp_loc_wikidata_concat.csv?",
                AUTO_FILE_LOCATIONS["nlp_loc_wikidata_concat"],
            )
            if not self.force
            else AUTO_FILE_LOCATIONS["nlp_loc_wikidata_concat"]
        )
        self.try_file(nlp_loc_wikidata_concat, False)

        df = pd.read_csv(nlp_loc_wikidata_concat, dtype={"NLP": str})

        for _, row in df.iterrows():
            if not Newspaper.objects.filter(publication_code=row.NLP):
                self.stdout.write(
                    self.style.WARNING(
                        f"NLP {row.NLP} not found in database => failed connection to gazetteer.Place with Wikidata ID {row['Wikidata ID']}."
                    )
                )
                continue

            if not Place.objects.filter(wikidata_id=row["Wikidata ID"]):
                self.stdout.write(
                    self.style.WARNING(
                        f"Wikidata ID {row['Wikidata ID']} not found in database => failed connection to newspaper.Newspaper {row.NLP}."
                    )
                )
                continue

            place_of_publication = Place.objects.get(wikidata_id=row["Wikidata ID"])
            for newspaper in Newspaper.objects.filter(publication_code=row.NLP):
                pub = newspaper
                pub.place_of_publication = place_of_publication
                pub.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"NLP {row.NLP} connected to gazetteer.Place {place_of_publication.id}."
                    )
                )

        self.special_write_fixture()
