import re
from datetime import datetime
from glob import glob
from logging import INFO, getLogger
from pathlib import Path
from typing import Callable, Final, Sequence

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import QuerySet
from tqdm import tqdm

DEFAULT_FIXTURE_PATH: Final[str] = "fixtures"
JSON_FORMAT_EXTENSION: Final[str] = ".json"

DEFAULT_MAX_LOG_STR_LENGTH: Final[int] = 30
DEFAULT_CALLABLE_CHUNK_SIZE: Final[int] = 20000
DEFAULT_CALLABLE_CHUNK_METHOD_NAME: Final[str] = "save"

DEFAULT_TRUNCATION_CHARS: Final[str] = "..."

DIGITS_REGEX: Final[str] = r"(\d+)"

NEWSPAPER_MODEL_NAME: Final[str] = "Newspaper"
ITEM_MODEL_NAME: Final[str] = "Item"

logger = getLogger(__name__)


def word_count(text: str) -> int:
    """Assuming English sentence structure, count words in `text`.

    Examples:
        >>> word_count("A big brown dog, left-leaning, loomed! Another joined.")
        8
    """
    return len(text.split())


def truncate_str(
    text: str,
    max_length: int = DEFAULT_MAX_LOG_STR_LENGTH,
    trail_str: str = DEFAULT_TRUNCATION_CHARS,
) -> str:
    """If `len(text) > max_length` return `text` followed by `trail_str`.

    Examples:
        >>> truncate_str('Standing on the shoulders of giants.', 15)
        'Standing on the...'
    """
    return text[:max_length] + trail_str if len(text) > max_length else text


def text2int(text: str) -> int | str:
    """If `text` is a sequence of digits convert `text` to `int`.

    Examples:
        >>> text2int('cat')
        'cat'
        >>> text2int('10')
        10
    """
    return int(text) if text.isdigit() else text


def natural_keys(
    text: str,
    split_regex: str = DIGITS_REGEX,
    func: Callable[[str], int | str] = text2int,
) -> list[str | int]:
    """Split `text` to strs via and numbers if possible via `func`.

    Designed for application to a list of fixture filenames with integers

    Examples:
        >>> example = ["fixture/Item-1.json", "fixture/Item-2.json", "fixture/Item-10.json"]
        >>> sorted(example, key=natural_keys)
        ['fixture/Item-1.json', 'fixture/Item-2.json', 'fixture/Item-10.json']

    Inspiration:
        http://nedbatchelder.com/blog/200712/human_sorting.html
    """
    return [func(c) for c in re.split(split_regex, text)]


def filter_starts_with(
    fixture_paths: Sequence[str],
    starts_with_str: str = NEWSPAPER_MODEL_NAME,
    key_func: Callable = natural_keys,
) -> list[str]:
    """Filter and sort `fixture_paths` that begin with `starts_with_str`.

    Examples:
        >>> paths = ['path/Newspaper-11.json', 'path/Issue-11.json', 'path/News-1.json']
        >>> filter_starts_with(fixture_paths=paths, starts_with_str="News")
        ['path/News-1.json', 'path/Newspaper-11.json']
    """
    return sorted(
        (
            f
            for f in fixture_paths
            if f.startswith(f"{Path(f).parent}/{starts_with_str}")
        ),
        key=key_func,
    )


def filter_exclude_starts_with(
    fixture_paths: Sequence[str],
    starts_str1: str = ITEM_MODEL_NAME,
    starts_str2: str = NEWSPAPER_MODEL_NAME,
    key_func: Callable = natural_keys,
) -> list[str]:
    """Exclude sort `fixture_paths` starting with `starts_str1`, `starts_str1`.

    Examples:
        >>> filter_exclude_starts_with(['path/Newspaper-11.json', 'path/Issue-11.json',
        ...                             'path/Item-1.json', 'cat'])
        ['cat', 'path/Issue-11.json']
    """
    return sorted(
        (
            f
            for f in fixture_paths
            if not f.startswith(f"{Path(f).parent}/{starts_str1}")
            and not f.startswith(f"{Path(f).parent}/{starts_str2}")
        ),
        key=key_func,
    )


def sort_all_fixture_paths(
    unsorted_fixture_paths: Sequence[str], key_func: Callable = natural_keys
) -> list[str]:
    """Sort fixture paths to correct order for importing.

    Examples:
        >>> paths = [
        ...     'path/Item-1.json', 'path/Newspaper-11.json',
        ...     'path/Issue-11.json', 'cat'
        ... ]
        >>> sort_all_fixture_paths(paths)
        ['path/Newspaper-11.json', 'cat', 'path/Issue-11.json', 'path/Item-1.json']
    """
    newspaper_fixture_paths: list[str] = filter_starts_with(
        unsorted_fixture_paths, NEWSPAPER_MODEL_NAME, key_func
    )
    non_newspaper_non_item_fixture_paths: list[str] = filter_exclude_starts_with(
        fixture_paths=unsorted_fixture_paths,
        key_func=key_func,
    )
    item_fixtures: list[str] = filter_starts_with(
        unsorted_fixture_paths, ITEM_MODEL_NAME, key_func
    )
    return (
        newspaper_fixture_paths + non_newspaper_non_item_fixture_paths + item_fixtures
    )


def get_fixture_paths(
    folder_path: Path | str = DEFAULT_FIXTURE_PATH,
    format_extension: str = JSON_FORMAT_EXTENSION,
) -> list[str]:
    """Return paths matching `folder_path` ending with `format_extension`."""
    return glob(f"{folder_path}/*{format_extension}")


def log_and_django_terminal(
    message: str,
    terminal_print: bool = False,
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
    if terminal_print:
        print(message)
    if django_command_instance:
        if style:
            django_command_instance.stdout.write(style(message))
        else:
            django_command_instance.stdout.write(message)


def callable_on_chunks(
    qs: QuerySet,
    method_name: str = DEFAULT_CALLABLE_CHUNK_METHOD_NAME,
    start_index: int | None = None,
    end_index: int | None = None,
    chunk_size: int = DEFAULT_CALLABLE_CHUNK_SIZE,
    terminal_print: bool = False,
    **kwargs,
) -> None:
    """Apply `method_name` to `qs`, filter by `start_index` and `end_index`."""
    model_name: str = qs.model.__name__
    log_and_django_terminal(
        f"Running `{method_name}` method on `{model_name}` QuerySet.",
        terminal_print=terminal_print,
    )

    start_time: datetime = datetime.now()
    qs_len: int = qs.count()
    post_count_time: datetime = datetime.now()

    count_to_process: int = (end_index or qs_len) - (start_index or 0)
    log_and_django_terminal(
        f"Queryset length: {count_to_process}", terminal_print=terminal_print
    )
    log_and_django_terminal(
        f"Queryset count time: {post_count_time - start_time}",
        terminal_print=terminal_print,
    )
    try:
        assert count_to_process >= 0
        if start_index:
            assert start_index < qs_len
        if end_index:
            assert end_index < qs_len
    except AssertionError:
        IndexError(
            (
                f"Invaid indexing for model {model_name}: `start_index` {start_index}, `end_index`: {end_index}, ",
                f"estimated record count: {count_to_process}.",
            )
        )

    start_index_str: str = str(start_index or 0)
    end_index_str: str = str(end_index or qs_len)
    log_and_django_terminal(
        f"Starting to processes {count_to_process} {model_name} records at {start_time}",
        terminal_print=terminal_print,
    )
    log_and_django_terminal(
        f"Chunksize set to {chunk_size}", terminal_print=terminal_print
    )
    log_and_django_terminal(
        f"Applying {method_name} from records {start_index_str} to {end_index_str} of {qs_len} of model `{model_name}`",
        terminal_print=terminal_print,
    )
    if kwargs:
        log_and_django_terminal(
            f"Parameters provided for {method_name}: {kwargs}",
            terminal_print=terminal_print,
        )

    for record in tqdm(
        qs[start_index:end_index].iterator(chunk_size=chunk_size),
        total=count_to_process,
    ):
        getattr(record, method_name)(**kwargs)
    end_time = datetime.now()
    log_and_django_terminal(
        f"Processed records {start_index_str} to {end_index_str} (total {count_to_process}) of {qs_len} {model_name} at {end_time}.",
        terminal_print=terminal_print,
    )
    log_and_django_terminal(
        f"Toral process time: {end_time - post_count_time}",
        terminal_print=terminal_print,
    )
    if count_to_process:
        log_and_django_terminal(
            f"Average process time: {(end_time - post_count_time)/count_to_process}",
            terminal_print=terminal_print,
        )


def import_fixtures(
    ordered_fixture_paths: list[str],
    start_index: int | None = None,
    end_index: int | None = None,
    django_command_instance: BaseCommand | None = None,
) -> None:
    """Call `loaddata` on fixtuers in `ordered_fixture_paths`."""
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
