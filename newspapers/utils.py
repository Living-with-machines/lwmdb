import re
from datetime import datetime
from glob import glob
from logging import INFO, getLogger
from pathlib import Path
from typing import Callable, Final, Sequence

from django.core.management import call_command
from django.core.management.base import BaseCommand

DEFAULT_FIXTURE_PATH: Final[str] = "fixtures"
JSON_FORMAT_EXTENSION: Final[str] = ".json"

logger = getLogger(__name__)


def text2int(text: str) -> int | str:
    return int(text) if text.isdigit() else text


def natural_keys(text: str) -> list[str | int]:
    """Alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html."""
    return [text2int(c) for c in re.split(r"(\d+)", text)]


def filter_news_fixtures(
    fixture_paths: Sequence[str],
    key_func: Callable = natural_keys,
) -> list[str]:
    return sorted(
        (f for f in fixture_paths if f.startswith(f"{Path(f).parent}/News")),
        key=key_func,
    )


def filter_non_news_non_item_fixtures(
    fixture_paths: Sequence[str],
    key_func: Callable = natural_keys,
) -> list[str]:
    return sorted(
        (
            f
            for f in fixture_paths
            if not f.startswith(f"{Path(f).parent}/Item-")
            and not f.startswith(f"{Path(f).parent}/News")
        ),
        key=key_func,
    )


def filter_item_fixtures(
    fixture_paths: Sequence[str], key_func: Callable = natural_keys
) -> list[str]:
    return sorted(
        (f for f in fixture_paths if f.startswith(f"{Path(f).parent}/Item-")),
        key=key_func,
    )


def sort_all_fixture_paths(
    unsorted_fixture_paths: Sequence[str], key_func: Callable = natural_keys
) -> list[str]:
    """Sort fixture paths to correct order for importing."""
    newspaper_fixture_paths: list[str] = filter_news_fixtures(
        unsorted_fixture_paths, key_func
    )
    non_newspaper_non_item_fixture_paths: list[str] = filter_non_news_non_item_fixtures(
        unsorted_fixture_paths, key_func
    )
    item_fixtures: list[str] = filter_item_fixtures(unsorted_fixture_paths, key_func)
    return (
        newspaper_fixture_paths + non_newspaper_non_item_fixture_paths + item_fixtures
    )


def get_fixture_paths(
    folder_path: Path | str = DEFAULT_FIXTURE_PATH,
    format_extension: str = JSON_FORMAT_EXTENSION,
) -> list[str]:
    return glob(f"{folder_path}/*{format_extension}")


def log_and_django_terminal(
    message: str,
    level: int = INFO,
    django_command_instance: BaseCommand | None = None,
    style: Callable | None = None,
    *arg,
    **kwargs,
) -> None:
    """Log and add Django formatted print to terminal if available.

    See: https://code.djangoproject.com/ticket/21429
    """
    logger.log(level, message, *arg, **kwargs)
    if django_command_instance:
        if style:
            django_command_instance.stdout.write(style(message))
        else:
            django_command_instance.stdout.write(message)


def import_fixtures(
    ordered_fixture_paths: list[str],
    start_index: int | None = None,
    end_index: int | None = None,
    django_command_instance: BaseCommand | None = None,
) -> None:
    success_style = (
        django_command_instance.style.SUCCESS if django_command_instance else None
    )
    tstart = datetime.now()
    log_and_django_terminal(
        f"Starting: {tstart}",
        django_command_instance=django_command_instance,
        style=success_style,
    )
    fixture_paths: list[str] = ordered_fixture_paths[start_index:end_index]
    for i, path in enumerate(fixture_paths):
        t1 = datetime.now()
        log_and_django_terminal(
            f"Starting import {i+1} of {len(fixture_paths)}: {t1}",
            django_command_instance=django_command_instance,
            style=success_style,
        )
        call_command("loaddata", path, verbosity=3)
        t2 = datetime.now()
        log_and_django_terminal(
            f"Import of path {path} took: {t2 - t1}",
            django_command_instance=django_command_instance,
            style=success_style,
        )
        log_and_django_terminal(
            f"Import time thus far: {t2 - tstart}",
            django_command_instance=django_command_instance,
            style=success_style,
        )
