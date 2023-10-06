import json
import re
from collections import defaultdict
from collections.abc import Callable, Generator, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from glob import glob
from logging import ERROR, INFO, WARNING, getLogger
from os import PathLike
from pathlib import Path
from shutil import copyfileobj
from tempfile import NamedTemporaryFile
from types import ModuleType
from typing import Any, Final, TypedDict
from urllib.error import URLError
from urllib.request import urlopen

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import Count, Field, Model, QuerySet
from pandas import DataFrame, Series
from tqdm import tqdm
from validators.url import url as validate_url

logger = getLogger(__name__)

VALID_TRUE_STRS: Final[tuple[str, ...]] = ("y", "yes", "t", "true", "on", "1")
VALID_FALSE_STRS: Final[tuple[str, ...]] = ("n", "no", "f", "false", "off", "0")

DEFAULT_FIXTURE_PATH: Final[str] = "fixtures"
JSON_FORMAT_EXTENSION: Final[str] = ".json"

DEFAULT_MAX_LOG_STR_LENGTH: Final[int] = 30
DEFAULT_CALLABLE_CHUNK_SIZE: Final[int] = 20000
DEFAULT_CALLABLE_CHUNK_METHOD_NAME: Final[str] = "save"

DEFAULT_TRUNCATION_CHARS: Final[str] = "..."

DIGITS_REGEX: Final[str] = r"(\d+)"

# Note: importing these can cause a circular import, hence defining locally
NEWSPAPER_MODEL_NAME: Final[str] = "Newspaper"
ITEM_MODEL_NAME: Final[str] = "Item"

DEFAULT_APP_DATA_FOLDER: Final[Path] = Path("data")
DEFAULT_APP_FIXTURE_FOLDER: Final[Path] = Path(DEFAULT_FIXTURE_PATH)

StrOrField = str | Field
StrOrFieldTuple = tuple[StrOrField, ...]
StrOrFieldIter = Iterable[StrOrField]

EXCLUDE_DUPE_FIELDS_DEFAULT: Final[tuple[StrOrField, ...]] = ("id",)
EXCLUDE_SIMILAR_TO_QS_FIELDS_DEFAULT: Final[tuple[StrOrField, ...]] = ("id__count",)


class JSONFixtureType(TypedDict):
    """A type to check `JSON` fixture structure."""

    pk: str
    model: str
    fields: dict[str, Any]


def str_to_bool(
    val: str,
    true_strs: Sequence[str] = VALID_TRUE_STRS,
    false_strs: Sequence[str] = VALID_FALSE_STRS,
) -> bool:
    """Convert values of `true_strs` to `True` and `false_strs` to `False`.

    Note:
        See
        https://docs.python.org/3/distutils/apiref.html#distutils.util.strtobool
        which is due to depricate, hence equivalent below.

    Args:
        var: `str` to convert into a `bool`
        true_strs: a `Sequence` of `str` values treated as `True`
        false_strs: a `Sequence` of `str` values treated as `False`

    Returns:
        `True` if `val` in `true_strs`, `False` if `val` in `false_str`.

    Raises:
        ValueError: if `val`, lowercased, is not a `str` in the `true_strs`
        or `false_strs`.

    Example:
        ```pycon
        >>> str_to_bool('true')
        True
        >>> str_to_bool('FaLSe')
        False
        >>> str_to_bool('Truely')
        Traceback (most recent call last):
        ...
        ValueError: `Truely` dose not match `True` values:
        ('y', 'yes', 't', 'true', 'on', '1')
        or `False` values:
        ('n', 'no', 'f', 'false', 'off', '0')

        ```
    """
    if val.lower() in true_strs:
        return True
    elif val.lower() in false_strs:
        return False
    else:
        raise ValueError(
            f"`{val}` dose not match `True` values:"
            f"\n{true_strs}\n"
            f"or `False` values:"
            f"\n{false_strs}"
        )


def word_count(text: str) -> int:
    """Assuming English sentence structure, count words in `text`.

    Args:
        text: text to count words from

    Returns:
        Count of words `text`.

    Example:
        ```pycon
        >>> word_count("A big brown dog, left-leaning, loomed! Another joined.")
        8

        ```
    """
    return len(text.split())


def truncate_str(
    text: str,
    max_length: int = DEFAULT_MAX_LOG_STR_LENGTH,
    trail_str: str = DEFAULT_TRUNCATION_CHARS,
) -> str:
    """If `len(text) > max_length` return `text` followed by `trail_str`.

    Args:
        text: `str` to truncate
        max_length: maximum length of `text` to allow, anything belond truncated
        trail_str: what is appended to the end of `text` if truncated

    Returns:
        `text` truncated to `max_length` (if longer than `max_length`),
        appended with `tail_str`

    Example:
        ```pycon
        >>> truncate_str('Standing in the shadows of love.', 15)
        'Standing in the...'

        ```
    """
    return text[:max_length] + trail_str if len(text) > max_length else text


def text2int(text: str) -> int | str:
    """If `text` is a sequence of digits convert `text` to `int`.

    Args:
        text: `str` to convert to `int` if possible

    Returns:
        `int` if `text` is a number, else the original `text`

    Example:
        ```pycon
        >>> text2int('cat')
        'cat'
        >>> text2int('10')
        10

        ```
    """
    return int(text) if text.isdigit() else text


def natural_keys(
    text: str,
    split_regex: str = DIGITS_REGEX,
    func: Callable[[str], int | str] = text2int,
) -> list[str | int]:
    """Split `text` to strs and/or numbers if possible via `func`.

    Designed for application to a list of fixture filenames with integers

    Args:
        text: `str` instance to process as a key
        split_regex: a regular expression to split keys, default extracts digits
        func:
            function to call on the results of `split_regex`, the results are
            can be used with `sorted` for ordering.

    Example:
        ```pycon
        >>> example = ["fixture/Item-1.json", "fixture/Item-10.json", "fixture/Item-2.json"]
        >>> sorted(example, key=natural_keys)
        ['fixture/Item-1.json', 'fixture/Item-2.json', 'fixture/Item-10.json']

        ```

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

    Example:
        ```pycon
        >>> paths = ['path/Newspaper-11.json', 'path/Issue-11.json', 'path/News-1.json']
        >>> filter_starts_with(fixture_paths=paths, starts_with_str="News")
        ['path/News-1.json', 'path/Newspaper-11.json']

        ```
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

    Example:
        ```pycon
        >>> filter_exclude_starts_with(['path/Newspaper-11.json', 'path/Issue-11.json',
        ...                             'path/Item-1.json', 'cat'])
        ['cat', 'path/Issue-11.json']

        ```
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
    """Sort fixture paths for `Newspaper.models` with order compatibility.

    Certain models within the `newspapers` `app` require a specific order to correctly
    import fixtures. This is written for potential generic application but primarily ment
    for `fixtures` including `newspapers` tables.

    Args:
        unsorted_fixture_paths: `Sequence` of `str` `fixture` paths to sort
        key_fun: function to call to order `unsorted_fixture_paths`

    Returns:
        `list` of sorted paths `str` via `key_func`

    Example:
        ```pycon
        >>> paths = [
        ...     'path/Item-1.json', 'path/Newspaper-11.json',
        ...     'path/Issue-11.json', 'cat'
        ... ]
        >>> sort_all_fixture_paths(paths)
        ['path/Newspaper-11.json', 'cat', 'path/Issue-11.json', 'path/Item-1.json']

        ```
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
    """Return paths matching `folder_path` ending with `format_extension`.

    Args:
        folder_path: folder to search for `fixtures` in
        format_extension: filename fromat extension suffix for filtering results

    Returns:
        `list` of file path `str` with `format_extension` suffix

    Example:
        ```pycon
        >>> sorted(get_fixture_paths('lwmdb/tests/'))  # doctest: +NORMALIZE_WHITESPACE
        ['lwmdb/tests/initial-test-dataprovider.json',
         'lwmdb/tests/update-test-dataprovider.json']
        >>> (
        ...     get_fixture_paths('lwmdb/tests/') ==
        ...     get_fixture_paths(Path('lwmdb') / 'tests')
        ... )
        True

        ```
    """
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

    Note:
        See: https://code.djangoproject.com/ticket/21429

    Args:
        messsage: `str` to log and potential print to terminal
        terminal_print: whether to print  to terminal as well
        level: what `logger` level to create
        django_command_instance:
            `BaseCommand` or subclass instance to manage `terminal interaction`
        style:
            function to call on `message` prior to sending to
            `django_command_instance` if provided. No effect
            without `django_command_instance`
        args: any positional arguments to send to `logger.log` call
        kwargs: keyword arguments  to pass to `logger.log` call

    Returns:
        None
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
    """Apply `method_name` to `qs`, filter by `start_index` and `end_index`.

    Args:
        qs: `django` `QerySet` instance to apply `method_name` total
        method_name: `Callable` `method` of `qs` `class` to apply to `qs`
        start_index: `int` of `qs` start point to apply `method_name` from
        end_index: `int` of `qs` end point to apply `method_name` to
        chunk_size: `int` for how many instance to batch process at a time
        terminal_print: whether to print logs to terminal

    Returns:
        None
    """
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


def download_file(
    local_path: PathLike, url: str, force: bool = False, terminal_print: bool = True
) -> bool:
    """If `force` or not available, download `url` to `local_path`.

    Example:
        ```pycon
        >>> jpg_url: str = "https://commons.wikimedia.org/wiki/File:Wassily_Leontief_1973.jpg"
        >>> local_path: Path = Path('test.jpg')
        >>> local_path.unlink(missing_ok=True)  # Ensure png deleted
        >>> success: bool = download_file(local_path, jpg_url)
        test.jpg not found, downloading from https://commons.wikimedia.org/wiki/File:Wassily_Leontief_1973.jpg
        https://commons.wikimedia.org/wiki/File:Wassily_Leontief_1973.jpg file available from test.jpg
        >>> success
        True
        >>> local_path.unlink()  # Delete downloaded jpg

        ```
    """
    local_path = Path(local_path)
    if not validate_url(url):
        log_and_django_terminal(
            f"{url} is not a valid url", terminal_print=terminal_print, level=ERROR
        )
        return False
    if not local_path.exists() or force:
        if force:
            log_and_django_terminal(
                f"Overwriting {local_path} by downloading from {url}",
                terminal_print=terminal_print,
            )
        else:
            log_and_django_terminal(
                f"{local_path} not found, downloading from {url}",
                terminal_print=terminal_print,
            )
        try:
            with (
                urlopen(url) as response,
                open(str(local_path), "wb") as out_file,
            ):
                copyfileobj(response, out_file)
        except IsADirectoryError:
            log_and_django_terminal(
                f"{local_path} must be a file, not a directory",
                terminal_print=terminal_print,
                level=ERROR,
            )
            return False
        except URLError:
            log_and_django_terminal(
                f"Download error (likely no internet connection): {url}",
                terminal_print=terminal_print,
                level=ERROR,
            )
            return False
        else:
            log_and_django_terminal(f"Saved to {local_path}")
    if not local_path.is_file():
        log_and_django_terminal(
            f"{local_path} is not a file", terminal_print=terminal_print, level=ERROR
        )
        return False
    if not local_path.stat().st_size > 0:
        log_and_django_terminal(
            f"{local_path} from {url} is empty",
            terminal_print=terminal_print,
            level=ERROR,
        )
        return False
    else:
        log_and_django_terminal(
            f"{url} file available from {local_path}",
            terminal_print=terminal_print,
        )
        return True


def app_data_path(app_name: str, data_path: PathLike = DEFAULT_APP_DATA_FOLDER) -> Path:
    """Return `app_name` data `Path` and ensure exists.

    Example:
        ```pycon
        >>> app_data_path('mitchells')
        PosixPath('mitchells/data')

        ```
    """
    path = Path(app_name) / Path(data_path)
    path.mkdir(exist_ok=True)
    return path


def _short_text_trunc(text: str, trail_str: str = DEFAULT_TRUNCATION_CHARS) -> str:
    """Return a `str` truncated to 15 characters followed by `trail_str`."""
    return truncate_str(
        text=text, trail_str=trail_str + path_or_str_suffix(text), max_length=15
    )


def path_or_str_suffix(
    str_or_path: str | PathLike,
    max_extension_len: int = 10,
    force: bool = False,
    split_str: str = ".",
) -> str:
    """Return suffix of `str_or_path`, else ''.

    Example:
        ```pycon
        >>> path_or_str_suffix('https://lwmd.livingwithmachines.ac.uk/file.bz2')
        'bz2'

        >>> path_or_str_suffix('https://lwmd.livingwithmachines.ac.uk/file')
        ''

        >>> path_or_str_suffix(Path('cat') / 'dog' / 'fish.csv')
        'csv'
        >>> path_or_str_suffix(Path('cat') / 'dog' / 'fish')
        ''

        ```
    """
    suffix: str = ""
    if isinstance(str_or_path, Path):
        if str_or_path.suffix:
            suffix = str_or_path.suffix[1:]  # Skip the `.` for consistency
        else:
            """"""
    else:
        split_str_or_path: list[str] = str(str_or_path).split(split_str)
        if len(split_str_or_path) > 1:
            suffix = split_str_or_path[-1]
            if "/" in suffix:
                log_and_django_terminal(
                    f"Split via {split_str} of "
                    f"{str_or_path} has a `/` `char`. "
                    "Returning ''",
                    level=ERROR,
                )
                return ""
        else:
            log_and_django_terminal(
                f"Can't split via {split_str} in "
                f"{_short_text_trunc(str(str_or_path))}",
                level=ERROR,
            )
            return ""
    if len(suffix) > max_extension_len:
        if force:
            log_and_django_terminal(f"Force return of suffix {suffix}", level=WARNING)
            return suffix
        else:
            log_and_django_terminal(
                f"suffix {_short_text_trunc(suffix)} too long "
                f"(max={max_extension_len})",
                level=ERROR,
            )
            return ""
    else:
        return suffix


class DataSourceDownloadError(Exception):
    ...


@dataclass
class DataSource:
    """Class to manage storing/deleting data files.

    Example:
        ```pycon
        >>> import census
        >>> from pandas import read_csv

        >>> rsd_1851: DataSource = DataSource(
        ...     file_name="demographics_england_wales_2015.csv",
        ...     app=census,
        ...     url="https://reshare.ukdataservice.ac.uk/853547/4/1851_RSD_data.csv",
        ...     read_func=read_csv,
        ...     description="Demographic and socio-economic variables for Registration Sub-Districts (RSDs) in England and Wales, 1851",
        ...     citation="https://dx.doi.org/10.5255/UKDA-SN-853547",
        ...     license="http://creativecommons.org/licenses/by/4.0/",
        ... )
        >>> rsd_1851.delete()  # To ensure it passes tests and doesn't fail
        >>> df = rsd_1851.read()
        census/data/demographics_england_wales_2015.csv not found, downloading from https://reshare.ukdataservice.ac.uk/853547/4/1851_RSD_data.csv
        https://reshare.ukdataservice.ac.uk/853547/4/1851_RSD_data.csv file available from census/data/demographics_england_wales_2015.csv
        >>> df.columns[:5].tolist()
        ['CEN_1851', 'REGCNTY', 'REGDIST', 'SUBDIST', 'POP_DENS']
        >>> rsd_1851.delete()

        ```
    """

    file_name: PathLike | str
    app: ModuleType
    url: str
    read_func: Callable[[PathLike], DataFrame | Series]
    description: str | None = None
    citation: str | None = None
    license: str | None = None
    _download_exception: DataSourceDownloadError | None = None
    _str_truncation_length: int = 15

    def __str__(self) -> str:
        """Readable description of which `file_name` from which `app`."""
        return (
            f"'{_short_text_trunc(str(self.file_name))}' "
            f"for `{self.app.__name__}` app data"
        )

    def __repr__(self) -> str:
        """Detailed, truncated reprt of `file_name` for `app`."""
        return (
            f"{self.__class__.__name__}({self.app.__name__!r}, "
            f"'{_short_text_trunc(str(self.file_name))}')"
        )

    @property
    def url_suffix(self) -> str:
        """Return suffix of `self.url` or None if not found."""
        return path_or_str_suffix(self.url)

    @property
    def _trunc_url_str_suffix(self) -> str:
        """Return DEFAULT_TRUNCATION_CHARS + `self.url_suffix`."""
        return DEFAULT_TRUNCATION_CHARS + self.url_suffix

    def _file_name_truncated(self) -> str:
        """Return truncated `file_name` for logging."""
        return truncate_str(
            text=Path(self.file_name).suffix,
            max_length=self._str_truncation_length,
            trail_str=self._trunc_url_str_suffix,
        )

    @property
    def local_path(self) -> Path:
        """Return path to store `self.file_name`."""
        return app_data_path(self.app.__name__) / self.file_name

    @property
    def is_empty(self) -> bool:
        """Return if `Path` to store `self.file_name` has 0 file size."""
        return self.local_path.stat().st_size == 0

    @property
    def is_file(self) -> bool:
        """Return if `self.local_path` is a file."""
        return self.local_path.is_file()

    @property
    def is_local(self) -> bool:
        """Return if `self.url` is storred locally at `self.file_name`."""
        return self.is_file and not self.is_empty

    def download(self, force: bool = False) -> bool:
        """Download `self.url` to save locally at `self.file_name`."""
        if self.is_local and not force:
            log_and_django_terminal(
                f"{self} already downloaded " f"(add `force=True` to override)"
            )
            return True
        else:
            return download_file(self.local_path, self.url)

    def delete(self) -> None:
        """Delete local save of `self.url` at `self.file_name`.

        Note:
            No error raised if missing.
        """
        log_and_django_terminal(f"Deleting local copy of {self} at {self.local_path}")
        self.local_path.unlink(missing_ok=True)

    def read(self, force: bool = False) -> DataFrame | Series:
        """Return data in `self.local_path` processed by `self.read_func`."""
        if not self.is_local:
            success: bool = self.download(force=force)
            if not success:
                self._download_exception = DataSourceDownloadError(
                    f"Failed to access {self} data from {self.url}"
                )
                logger.error(str(self._download_exception))
        return self.read_func(self.local_path)


class ModelUpdateDict(TypedDict):
    instances: list[Model]
    fields: set[str]


def bulk_fixture_update(
    fixture_path: PathLike,
    create_new_records: bool = False,
    batch_size: int = 1000,
) -> None:
    """Modify existing records with fixture.

    Args:
        fixture_path:
            `Path` of fixture to update from
        create_new_records:
            Whether to add new records as well as updated fixtures
        batch_size:
            Size for batch record updates (not applied to new records)

    Example:
        ```pycon
        >>> getfixture("db")
        >>> getfixture("old_data_provider")
        Installed 4 object(s) from 1 fixture(s)
        >>> updated_fixture_path = getfixture("updated_data_provider_path")
        >>> from newspapers.models import DataProvider
        >>> for provider in DataProvider.objects.all():
        ...     print(provider)
        bna
        hmd
        jisc
        lwm
        >>> bulk_fixture_update(fixture_path=updated_fixture_path)
        >>> for provider in DataProvider.objects.all():
        ...     print(provider)
        FindMyPast
        Heritage Made Digital
        Joint Information Systems Committee
        Living with Machines
        >>> bulk_fixture_update(fixture_path=updated_fixture_path,
        ...                     create_new_records=True)
        Installed 1 object(s) from 1 fixture(s)
        >>> for provider in DataProvider.objects.all():
        ...     print(provider)
        FindMyPast
        Heritage Made Digital
        Joint Information Systems Committee
        Living with Machines
        Example New Provider

        ```
    """
    records_to_update: defaultdict[type[Model], ModelUpdateDict] = defaultdict(
        lambda: ModelUpdateDict(instances=[], fields=set()),
    )
    records_to_create: list[JSONFixtureType] = []
    with open(fixture_path) as fixture:
        record_dict: JSONFixtureType
        for record_dict in json.loads(fixture.read()):
            model_type: Model = apps.get_model(record_dict["model"])
            model_instance: Model | None = model_type.objects.filter(
                pk=record_dict["pk"]
            ).first()
            if model_instance:
                for db_field, value in record_dict["fields"].items():
                    setattr(model_instance, db_field, value)
                    records_to_update[model_type]["fields"].add(db_field)
                records_to_update[model_type]["instances"].append(model_instance)
            else:
                records_to_create.append(record_dict)
    updated_records: dict[type[Model], list[Model]] = {}
    model: Model
    updates_dict: ModelUpdateDict
    for model, updates_dict in records_to_update.items():
        log_and_django_terminal(
            f"Bulk updating {len(updates_dict['instances'])} {model} instances\n"
            f"Fields to update: {updates_dict['fields']}",
        )
        updated_records[model] = model.objects.bulk_update(
            updates_dict["instances"], updates_dict["fields"], batch_size=batch_size
        )
    if create_new_records:
        with NamedTemporaryFile(mode="w", suffix=".json") as new_fixtures_tempfile:
            json.dump(records_to_create, fp=new_fixtures_tempfile)
            new_fixtures_tempfile.flush()
            call_command("loaddata", new_fixtures_tempfile.name)


# def attr_str_to_field(model: Model, field_name: str, strict=True) -> Field | None:
#     """Check and return `field_name` of `model`.
#
#     """
#     try:
#         assert hasattr(model, field_name):
#     except AssertionError as attr_err:
#         if strict:
#             raise AttributeError(f"`model` {model} has {field_name} field.")
#         else:
#             return None
#     return getattr(model, field_name)


def check_model_field(model: Model, db_field: StrOrField) -> Field:
    """Check `fields` is correct for `self`.

    Example:
        ```pycon
        >>> from newspapers.models import Newspaper
        >>> check_model_field(Newspaper, 'title')
        <django.db.models.fields.CharField: title>
        >>> check_model_field(Newspaper, Newspaper._meta.get_field('title'))
        <django.db.models.fields.CharField: title>

        ```

    check_model_field(Newspaper, 'name')
    <BLANKLINE>
    ...FieldDoesNotExist: Newspaper has no field named 'name'...
    """
    if isinstance(db_field, str):
        return model._meta.get_field(db_field)
    else:
        assert hasattr(model, db_field.name)
        return db_field


def foreign_key_fields(model: Model) -> Generator[Field, None, None]:
    """Yield all `model` `ForeignKey` `Fields`.

    Args:
        model: `Model` to retrive `ForeignKey` fields from.

    Yields:
        Each `ForeignKey` from `Model`.

    Example:
        ```pycon
        >>> from newspapers.models import Issue
        >>> tuple(foreign_key_fields(Issue))
        (<ManyToOneRel: newspapers.item>,
         <django.db.models.fields.related.ForeignKey: newspaper>)

        ```
    """
    for db_field in model._meta.get_fields():
        if db_field.is_relation:
            yield db_field


def convert_similar_qs_to_records(
    similar_records_qs: QuerySet,
    exclude_fields: StrOrFieldTuple = EXCLUDE_SIMILAR_TO_QS_FIELDS_DEFAULT,
) -> QuerySet:
    """Convert a summary_qs to full implied records.

    Examples:
        ```pycon
        >>> getfixture("db")
        >>> check_qs: QuerySet = getfixture("newspaper_dupes_qs")
        >>> from newspapers.models import Newspaper
        >>> qs = similar_records(check_qs, check_fields=('publication_code',))
        >>> qs
        <DataFrameQuerySet [{'publication_code': '0003548', 'id__count': 2}]>
        >>> convert_similar_qs_to_records(qs)
        <DataFrameQuerySet [0003548, 0003548]>

        ```
    """

    model: Model = similar_records_qs.model
    converted_records_qs: QuerySet = model.objects.all()
    for similar_counts in similar_records_qs:
        similar_counts_for_query: QuerySet = similar_counts
        for key in exclude_fields:
            if isinstance(key, Field):
                key = key.name
            similar_counts_for_query.pop(key, None)
        converted_records_qs = converted_records_qs.filter(**similar_counts_for_query)
    return converted_records_qs


def filter_by_not_all_null_fk(qs: QuerySet) -> tuple[QuerySet, QuerySet]:
    """Return a `tuple` of `QuerySets` from `qs`: None, at least one
    ForeignKey.

    Args:
        qs: `QuerySet` to filter from.

    Returns:
        First `QuerySet` has `None` values for all `ForeignKey` `Fields`, the
        second has at least one `not` `Null` `ForeignKey`.

    Example:
        ```pycon
        >>> getfixture("db")
        >>> caplog = getfixture("caplog")
        >>> dupe_qs: QuerySet = getfixture("newspaper_dupes_qs")
        >>> to_delete, to_keep = filter_by_not_all_null_fk(dupe_qs)
        >>> to_delete
        <DataFrameQuerySet [0003548, 0002648]>
        >>> to_delete.values_list('pk', flat=True)
        <DataFrameQuerySet [..., ...]>
        >>> to_keep  # Note same publication code as record above
        <DataFrameQuerySet [0003548]>
        >>> to_keep.values_list('pk', flat=True)  # But different `pk`
        <DataFrameQuerySet [...]>
        >>> to_keep.values('issue')  # The record to keep has an related `issue`
        <DataFrameQuerySet [{'issue': ...}]>
        >>> to_delete.values('issue')  # Neither record to delete have related `issues`
        <DataFrameQuerySet [{'issue': None}, {'issue': None}]>


        ```
    """
    fk_fields: tuple[Field] = tuple(foreign_key_fields(qs.model))
    records_with_all_fks_null: QuerySet = qs.all()
    for fk_field in fk_fields:
        filter_query_dict: dict[str, Any] = {fk_field.name + "__isnull": True}
        logger.debug(f"Filtering {qs} with {fk_field}")
        records_with_all_fks_null = records_with_all_fks_null.filter(
            **filter_query_dict
        )
    records_with_at_least_one_fk: QuerySet = qs.difference(records_with_all_fks_null)
    return records_with_all_fks_null, records_with_at_least_one_fk


@dataclass
class DupeRemoveConfig:
    """Configuration of potential duplication records for deletion.

    Attributes:
        all_dupe_records:
            Initial `QuerySet` to check duplicates in.

        records_to_delete:
            `QuerySet` of records to delete. Should be a subset of `all_dupe_records`.

        records_to_keep:
            `QuerySet` of records to keep (not delete). Should be a subset of
            `all_dupe_records`.

    Example:
        ```pycon
        >>> getfixture("db")
        >>> caplog = getfixture("caplog")
        >>> dupe_qs: QuerySet = getfixture("newspaper_dupes_qs")
        >>> dupe_config: DupeRemoveConfig = DupeRemoveConfig(
        ...     all_dupe_records=dupe_qs,)
        >>> dupe_config.records_to_delete
        <DataFrameQuerySet [0003548, 0002648]>
        >>> dupe_config.records_to_delete.values_list('pk', flat=True)
        <DataFrameQuerySet [..., ...]>
        >>> dupe_config.records_to_keep  # Same `publication_code` in __str__ as a record above
        <DataFrameQuerySet [0003548]>
        >>> dupe_config.records_to_keep.values_list('pk', flat=True)  # But different `pk`
        <DataFrameQuerySet [...]>
        >>> dupe_config.records_to_keep.values('issue')  # The record to keep has an related `issue`
        <DataFrameQuerySet [{'issue': ...}]>
        >>> dupe_config.records_to_delete.values('issue')  # Neither record to delete have related `issues`
        <DataFrameQuerySet [{'issue': None}, {'issue': None}]>

        ```
    """

    all_dupe_records: QuerySet | None = None
    records_to_delete: QuerySet | None = None
    records_to_keep: QuerySet | None = None
    dupe_method: Callable[
        [QuerySet], tuple[QuerySet, QuerySet]
    ] | None = filter_by_not_all_null_fk
    DELETED_RECORDS_ATTR: Final[str] = "records_last_deleted"

    def __len__(self) -> int:
        """Return `len` of `self.all_dupe_records`"""
        return len(self.all_dupe_records)

    @property
    def to_delete_count(self) -> int:
        """Return count of records to delete."""
        if self.records_to_delete:
            return len(self.records_to_delete)
        else:
            return 0

    @property
    def to_keep_count(self) -> int:
        """Return count of records to keep."""
        if self.records_to_keep:
            return len(self.records_to_keep)
        else:
            return 0

    @property
    def model(self) -> Model:
        return self.all_dupe_records.model

    def __repr__(self) -> str:
        """Return config as `str`"""
        return (
            f"<DupeRemoveConfig(model={self.model}, "
            f"len={len(self)}), valid={self.valid_config})>"
        )

    def set_records_to_keep_and_delete(self) -> None:
        """Apply `dupe_method` for `self.to_delete`/`keep` if both None."""
        if self.dupe_method and not self.records_to_delete and not self.records_to_keep:
            self.records_to_delete, self.records_to_keep = self.dupe_method(
                self.all_dupe_records
            )
        else:
            logger.info(
                "`self.records_to_delete` and/or "
                "`self.records_to_keep` are not None. "
                f"Set to None to generate for {self}"
            )

    def __post_init__(self) -> None:
        """Apply `self.set_records_to_keep_and_delete`."""
        self.set_records_to_keep_and_delete()

    @property
    def valid_config(self) -> bool:
        """Check `records_to_delete` and `records_to_keep` match
        `all_dupe_records`.

        Example:
            ```pycon
            >>> getfixture("db")
            >>> dupe_config = getfixture('newspaper_dupe_rm_config')
            >>> dupe_config.valid_config
            True
            >>> dupe_config.records_to_delete = None
            >>> dupe_config.valid_config
            False

            ```
        """
        if self.records_to_delete and self.records_to_keep:
            return set(self.all_dupe_records) == set(
                self.records_to_delete.union(self.records_to_keep)
            )
        else:
            return False

    def delete_records(
        self,
        dry_run: bool = True,
        check_queries: bool = True,
        force_repeat_delete: bool = True,
    ) -> tuple[int, dict] | QuerySet | None:
        """Delete records if `dry_run` is `False` and `check_queries` pass.

        Args:
            dry_run:
                Return the `records_to_delete` `QuerySet` if True, else delete
                all in `records_to_delete`.

            check_quries:
                Whether to run checks (currently `self.valid_config`) before

        Example:
            ```pycon
            >>> getfixture("db")
            >>> dupe_config = getfixture('newspaper_dupe_rm_config')
            >>> caplog = getfixture('caplog')
            >>> dupe_config.delete_records()
            <DataFrameQuerySet [0003548, 0002648]>
            >>> dupe_config.to_delete_count
            2
            >>> dupe_config.delete_records(dry_run=False)
            (2, {'newspapers.Newspaper': 2})
            >>> dupe_config.records_last_deleted
            (2, {'newspapers.Newspaper': 2})

            ```
        """
        if not self.records_to_delete:
            logger.info(
                f"{self} cannot delete: 'self.records_to_delete' is "
                f"{self.records_to_delete}"
            )
        if check_queries:
            try:
                assert self.valid_config
            except AssertionError:
                raise ValueError(
                    f"{self} has inconsistent counts for 'records_to_delete' "
                    f"and/or 'records_to_keep' attributes"
                )
        else:
            logger.warning(f"Applying `.delete()` without `.check_queries` to {self}")
        if not dry_run:
            if hasattr(self, self.DELETED_RECORDS_ATTR):
                prev_deleted_records = getattr(self, self.DELETED_RECORDS_ATTR)
                logger.info(
                    f"Records already deleted for {self}:\n" f"{prev_deleted_records}"
                )
                if force_repeat_delete:
                    logger.info(f"Removing 'self.deleted_records' for new delete")
                    del prev_deleted_records
            logger.info("Deleting {self.to_delete_count} via {self}")
            setattr(self, self.DELETED_RECORDS_ATTR, self.records_to_delete.delete())
            return getattr(self, self.DELETED_RECORDS_ATTR)
        else:
            return self.records_to_delete


# def _model_qs_check(qs: QuerySet | None, model: Model | None,) -> tuple[


def similar_records(
    qs: QuerySet,
    check_fields: tuple[str | Field, ...] = (),
    exclude_fields: tuple[str | Field, ...] = EXCLUDE_DUPE_FIELDS_DEFAULT,
) -> QuerySet:
    """Check for duplicate records in `model` and delete if not `dry_run`.

    Args:
        qs: `QuerySet` to check for duplicate records.
        check_fields: Fields in `Model` to check; default checks all.
        exclude_fields:
            Fields in `Model` to skip for comparision.
            Default `id` fields *must* be unique, as they are usually the
            primary key.

    Example:
        ```pycon
        >>> getfixture("db")
        >>> check_qs: QuerySet = getfixture("newspaper_dupes_qs")
        >>> from newspapers.models import Newspaper
        >>> similar_records(check_qs, check_fields=('publication_code',))
        <DataFrameQuerySet [{'publication_code': '0003548', 'id__count': 2}]>
        >>> similar_records(Newspaper.objects.all())
        <DataFrameQuerySet []>
        >>> similar_records(Newspaper.objects.all(),
        ...                 check_fields=('publication_code',))
        <DataFrameQuerySet [{'publication_code': '0003548', 'id__count': 2}]>

        ```
    """
    model: Model = qs.model
    model_fields: dict[str, Field] = {
        db_field.name: db_field for db_field in model._meta.get_fields()
    }
    if exclude_fields:
        check_fields = tuple(set(check_fields) - set(exclude_fields))

    return (
        qs.values(*check_fields)
        .annotate(Count("id"))
        .order_by()
        .filter(id__count__gt=1)
    )


def dupes_to_rm(
    qs_or_model: QuerySet | Model,
    dupe_fields: tuple[str | Field, ...] = (),
    exclude_fields: tuple[str | Field, ...] = EXCLUDE_SIMILAR_TO_QS_FIELDS_DEFAULT,
) -> DupeRemoveConfig | None:
    """Check for similar records and return a `DupeRemoveConfig` for deletion.

    Args:
        qs_or_model:
            `QuerySet` to filter from, or `Model` to filter all records from.
        dupe_fiel

    Example:
        ```pycon
        >>> getfixture("db")
        >>> dupe_qs: QuerySet = getfixture("newspaper_dupes_qs")
        >>> dupes_rm_config: DupeRemoveConfig = dupes_to_rm(dupe_qs,
        ...     dupe_fields=('publication_code',))
        >>> dupes_rm_config.delete_records()
        <DataFrameQuerySet [0003548]>
        >>> dupes_rm_config.delete_records(dry_run=False)
        (1, {'newspapers.Newspaper': 1})
        >>> dupes_rm_config.records_last_deleted
        (1, {'newspapers.Newspaper': 1})

        ```
    """
    model: Model
    qs: QuerySet

    if isinstance(qs_or_model, QuerySet):
        qs = qs_or_model
        model = qs_or_model.model
    else:
        model = qs_or_model
        qs = model.objects.all()

    similars_qs: QuerySet = similar_records(
        qs=qs, check_fields=dupe_fields, exclude_fields=exclude_fields
    )
    if not similars_qs:
        return None
    else:
        dupe_records: QuerySet = convert_similar_qs_to_records(similars_qs)
        return DupeRemoveConfig(dupe_records)


# @dataclass
# class DuplicateChecker:
#
#     """Check duplicates for correction.
#
#     Attributes:
#         model: `Model` to check for duplicate records in `sql`.
#         qs: `QuerySet` to check for duplicate records.
#         dupe_fields: Fields in `Model` to check; default checks all.
#         exclude_fields:
#             Fields in `Model` to skip for comparision. Default `id`
#             fields *must* be unique, as they are usually the primary
#             key.
#
#     Example:
#         ```pycon
#         >>> getfixture("db")
#         >>> dupe_qs: QuerySet = getfixture("newspaper_dupes_qs")
#         >>> checker = DuplicateChecker(model=dupe_qs.model)
#         >>> checker.dupes_to_rm()
#         >>> checker.get_dupes()
#         <DataFrameQuerySet []>
#         >>> db_dupes(Newspaper, dupe_fields=('publication_code',))
#         ... # doctest: +ELLIPSIS
#         <DataFrameQuerySet [{'publication_code': '0003548', 'id__count': 2}]>
#         >>> dupes_rm_config: DupeRemoveConfig = db_dupes.rm_config()
#         >>> dupe_rm_config.delete_records()
#         <DataFrameQuerySet [0003548, 0002648]>
#         >>> dupe_rm_config.delete_records(dry_run=False)
#         (2, {'newspapers.Newspaper': 2})
#         >>> dupe_rm_config.records_last_deleted
#         (2, {'newspapers.Newspaper': 2})
#
#         ```
#
#     """
#
#     EXCLUDE_FIELDS_DEFAULT: Final[tuple[str | Field, ...]] = ('id',),
#
#     model: Model | None = None
#     qs: QuerySet | None = None
#     dupe_fields: StrOrFieldTuple = field(default_factory=tuple),
#     exclude_fields: StrOrFieldTuple = field(default_factory=tuple),
#
#     def __post_init__(self) -> None:
#         """Check `model`, `qs`, `dupe_fields` and `exclude_fields`."""
#         self._set_qs_and_model(qs=self.qs, model=self.model)
#         self._set_fields_attrs(dupe_fields=self.dupe_fields,
#                                exclude_fields=self.exclude_fields)
#
#     # def _set_model(self, model: Model, force_set_model=False) -> Model:
#     #     """Set model and ensure it matches"""
#
#     def _set_qs_and_model(
#         self,
#         qs: QuerySet | None = None,
#         model: Model | None = None,
#         force_set_model: bool = False
#     ) -> None:
#         """Check and set `self.qs` and `self.model`.
#
#         Example:
#             pycon
#             getfixture("db")
#             dupe_newspaper_qs: QuerySet = getfixture("newspaper_dupes_qs")
#             dupe_checker: DuplicateChecker =
#
#         """
#         if not qs and not model:
#             raise ValueError(f"At least one of `qs` or `model` must be set.")
#         elif qs and model:
#             try:
#                 assert qs.model is model
#             except AssertionError:
#                 error_str: str = f"`qs.model`: {qs.model} != `model` {model}"
#                 if force_set_model:
#                     logger.warning(
#                         f"{error_str}\n'force_set_model' = True: "
#                         f"setting 'self.model' to 'qs.model': {self.qs.model}"
#                     )
#                 else:
#                     raise ValueError(error_str)
#         elif not self.model:
#             self.model = self.qs.model
#         else:
#             self.qs = self.model.objects.all()
#
#     def _set_fields_attrs(
#         self,
#         dupe_fields: StrOrFieldIter | None = None,
#         exclude_fields: StrOrFieldIter | None = None,
#     ) -> None:
#         """Check and update `dupe_fields` and `exclude_fields` `attrs`."""
#         if dupe_fields:
#             self._set_fields_attr('dupe_fields', dupe_fields)
#         if exclude_fields:
#             self._set_fields_attr('exclude_fields', exclude_fields, self.EXCLUDE_FIELDS_DEFAULT)
#
#     def _set_fields_attr(
#             self,
#             field_name: str,
#             values: StrOrFieldIter,
#             default_values: tuple = ()) -> None:
#         """Ensure `field_name` values are `Field"""
#         if not values:
#             setattr(self, field_name, default_values)
#         else:
#             values = tuple(
#                 check_model_field(self.model, db_field=field_name) for
#                 field_name in values if field_name
#             )
#             setattr(self, field_name, values)
#
#     @property
#     def model_fields_dict(self) -> dict[str, Field]:
#         """All fields in `self.model`."""
#         return {field.name: db_field for db_field in self.model._meta.get_fields()}
#
#     # @property
#     # def related_fields_dict(self) -> dict[str, Field]:
#     #     """All fields in `self.model`."""
#     #     return {
#     #         field.name: field for field in self.model._meta.get_fields()
#     #         if field.is_relation
#     #     }
#
#     @property
#     def final_dupe_fields(self) -> tuple[str, ...]:
#         """Final net `tuple` of fields to check duplication."""
#         return tuple(sorted(set(self.dupe_fields) - set(self.exclude_fields)))
#
#     def dupes_to_rm(
#             self,
#             from_cache: bool = True,
#             **kwargs
#         ) -> DupeRemoveConfig:
#         """Return a `DupeRemoveConfig` instance to prepare for deletion."""
#         dupe_ids: QuerySet
#         assert False
#         if not hasattr(self, '_dupe_ids') or not from_cache:
#             dupe_ids = self.dupe_ids(**kwargs)
#         else:
#             dupe_ids = self._dupe_ids
#         dupe_records: QuerySet = self.model.objects.filter(pk__in=dupe_ids)
#         self.rm_config: DupeRemoveConfig = DupeRemoveConfig(dupe_records)
#         return self.rm_config
#
#
#     # @dataclass
#     # class DupeRemoveConfig:
#     #     all_dupe_records: QuerySet
#     #     proposed_delete_records: QuerySet
#     #     proposed_saved_records: QuerySet
#
#
#     def dupe_ids(
#         self,
#         dupe_fields: StrOrFieldIter | None = None,
#         exclude_fields: StrOrFieldIter | None = None,
#         qs: QuerySet | None = None,
#         force_set_model: bool = False,
#         cache: bool = True,
#     ) -> QuerySet:
#         """Get dupes from `Model`; update `self.dupe_fields` and `self.exclude_fields`.
#
#         Todo:
#             Add log info of altering attributes
#
#         """
#         qs = qs if qs else self.qs
#         dupe_fields = dupe_fiels if dupe_fields else self.dupe_fields
#         exclude_fields = exclude_fields if exclude_fields else self.exclude_fields
#         self._set_qs_and_model(qs=qs, force_set_model=force_set_model)
#         self._set_fields_attrs(dupe_fields=dupe_fields, exclude_fields=exclude_fields)
#         dupe_qs: QuerySet = (
#             self.qs.values(*self.final_dupe_fields)
#                 .annotate(Count('id'))
#                 .order_by().filter(id__count__gt=1)
#         )
#         if cache:
#             self._dupe_ids: QuerySet = dupe_qs
#         return dupe_qs
