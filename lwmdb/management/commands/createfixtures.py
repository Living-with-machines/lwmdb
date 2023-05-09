from django.core.management import BaseCommand

from census.management.commands.census import CensusFixture
from gazetteer.management.commands.gazetteer import GazetteerFixture
from mitchells.management.commands.mitchells import MitchellsFixture
from newspapers.management.commands.items import ItemFixture
from newspapers.management.commands.newspapers import NewspapersFixture

from .fixtures import Connector

ALLOWED_APPS = [
    "gazetteer",
    "mitchells",
    "newspapers",
    "items",
    "census",
]  # this is the required order


class Command(BaseCommand):
    # Show this when the user types help
    help = "Creates fixtures for any given type of model"

    def add_arguments(self, parser):
        parser.add_argument(
            "app",
            type=str,
            nargs="+",
            help=(
                "Indicates the app(s) that you want to create "
                "fixtures for. You can use 'all' as shorthand "
                "for all allowed apps"
            ),
        )
        parser.add_argument(
            "-f", "--force", action="store_true", help='Force "yes" on all questions'
        )
        parser.add_argument(
            "--no_build",
            action="store_true",
            help="Skip building cache files",
            default=False,
        )

    def handle(self, *args, **kwargs):
        # Extract apps (and allow for "all" as app argument)
        apps = (
            ALLOWED_APPS
            if len(kwargs["app"]) == 1 and kwargs["app"][0] == "all"
            else kwargs["app"]
        )

        # Block if non-allowed apps passed
        exit(
            f"App(s) not allowed: {[x for x in apps if not x in ALLOWED_APPS]}",
        ) if [x for x in apps if not x in ALLOWED_APPS] else None

        for app in apps:
            if app == "gazetteer":
                creator = GazetteerFixture(force=kwargs.get("force"))
                creator.create_gazetteer_fixtures()
                creator.load_fixtures()
            elif app == "mitchells":
                creator = MitchellsFixture(force=kwargs.get("force"))
                creator.create_mitchells_fixtures()
                creator.load_fixtures()
            elif app == "census":
                creator = CensusFixture(force=kwargs.get("force"))
                creator.build_fixture()
            elif app == "newspapers":
                creator = NewspapersFixture(force=kwargs.get("force"))

                if kwargs.get("no_build") == False:
                    # First: build cache...
                    creator.build_cache()

                # Then: ingest cache...
                creator.ingest_cache()

                # Then: save fixtures (not necessary)
                # creator.save_fixtures()

            elif app == "items":
                creator = ItemFixture(force=kwargs.get("force"))

                if kwargs.get("no_build") == False:
                    # First: build cache...
                    creator.build_cache()

                # Then: ingest cache...
                # creator.ingest_cache()
        else:
            connector = Connector(force=kwargs.get("force"))
            connector.connect()

            if len(apps) > 1:
                self.stdout.write(self.style.SUCCESS("All done."))
