from django.core.management import BaseCommand

from .createfixtures import (
    ALLOWED_APPS,
    Connector,
    GazetteerFixture,
    MitchellsFixture,
    NewspapersFixture,
)


class Command(BaseCommand):
    help = "Loads fixtures for any given type of model"

    def add_arguments(self, parser):
        parser.add_argument(
            "app",
            type=str,
            nargs="+",
            help="Indicates the app(s) that you want to load fixtures for. You can use 'all' as shorthand for all allowed apps",
        )
        parser.add_argument(
            "-f", "--force", action="store_true", help='Force "yes" on all questions'
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
            if app == "newspapers":
                creator = NewspapersFixture(force=kwargs.get("force"))
                creator.app_name = "newspapers"
                creator.load_fixtures()
            elif app == "gazetteer":
                creator = GazetteerFixture(force=kwargs.get("force"))
                creator.app_name = "gazetteer"
                creator.load_fixtures()
            elif app == "mitchells":
                creator = MitchellsFixture(force=kwargs.get("force"))
                creator.app_name = "mitchells"
                creator.load_fixtures()

        else:
            connector = Connector(force=kwargs.get("force"))
            connector.connect()

            if len(apps) > 1:
                self.stdout.write(self.style.SUCCESS("All done."))
