from django.core.management import BaseCommand

from .fixtures import Connector

ALLOWED_APPS = [
    "gazetteer",
    "mitchells",
    "newspapers",
    "items",
]  # this is the required order


class Command(BaseCommand):
    # Show this when the user types help
    help = "Connects any related models"

    def add_arguments(self, parser):
        parser.add_argument(
            "-f", "--force", action="store_true", help='Force "yes" on all questions'
        )

    def handle(self, *args, **kwargs):
        connector = Connector(force=kwargs.get("force"))
        connector.connect()
