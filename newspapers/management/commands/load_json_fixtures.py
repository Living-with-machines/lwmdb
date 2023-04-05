from pathlib import Path

from django.core.management.base import BaseCommand

from ..utils import (
    DEFAULT_FIXTURE_PATH, JSON_FORMAT_EXTENSION, get_fixture_paths, sort_all_fixture_paths, import_fixtures
)


class Command(BaseCommand):

    """Load a collection of `json` data in the correct order."""

    help: str = "Loads all `json` files in the `fixtures` path in an enforced order"
    path: Path = Path(DEFAULT_FIXTURE_PATH)
    format_extension: str = JSON_FORMAT_EXTENSION

    def add_arguments(self, parser) -> None:
        parser.add_argument('--path', nargs='?', const=1, type=str, default=str(self.path))
        parser.add_argument('--start-index', nargs='?', const=1, type=int)
        parser.add_argument('--end-index', nargs='?', const=1, type=int)

    def handle(self, *args, **options) -> None:
        if options["path"]:
            self.path = Path(options["path"])
        start_index: int | None = options["start_index"] if options["start_index"] else None
        end_index: int | None = options["end_index"] if options["end_index"] else None
        self.stdout.write(
            self.style.SUCCESS(f'Loading fixtures from {self.path}')
        )
        self._unsorted_fixture_paths: list[str] = get_fixture_paths(self.path, self.format_extension)
        self.fixture_paths = sort_all_fixture_paths(self._unsorted_fixture_paths)
        import_fixtures(self.fixture_paths, start_index=start_index, end_index=end_index, django_command_instance=self)
