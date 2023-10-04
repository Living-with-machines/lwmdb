from enum import IntEnum, auto
from os import PathLike
from pathlib import Path
from typing import Final

ITEM_EXENSION: Final[str] = ".txt"
START_YEAR: Final[int] = 1800
FINAL_YEAR: Final[int] = 2000
MAX_MONTH_DAY_INT: Final[int] = 1231


class NewspaperCodeType(IntEnum):
    """Structure for managing data from `alto2txt`."""

    PUBLICATION = 0
    ISSUE = auto()
    ITEM = auto()


class Alto2txtPathError(Exception):
    ...


def path_to_newspaper_code(
    txt_path: PathLike,
    type: NewspaperCodeType | str | int = NewspaperCodeType.ITEM,
    item_suffix: str = ITEM_EXENSION,
    start_year: int = START_YEAR,
    final_year: int = FINAL_YEAR,
    max_month_day_int: int = MAX_MONTH_DAY_INT,
) -> str:
    """Convert `txt_path` into `NewspaperCodeType` format.

    Example:
        ```pycon
        >>> path_to_newspaper_code(
        ...     '0003548/1904/0707/0003548_19040707_art0037.txt')
        '0003548-19040707-art0037'
        >>> path_to_newspaper_code(
        ...     '0003548/1904/0707/0003548_19040707_art0037.txt',
        ...     "issue")
        '0003548-19040707'
        >>> path_to_newspaper_code(
        ...     '0003548/1904/0707/0003548_19040707_art0037.txt',
        ...     "publication")
        '0003548'

        ```
    """
    txt_path = Path(txt_path)
    if isinstance(type, str):
        type = NewspaperCodeType[type.upper()]
    elif isinstance(type, int):
        type = NewspaperCodeType(type)
    assert isinstance(type, NewspaperCodeType)
    if type == NewspaperCodeType.ITEM:
        if txt_path.suffix == item_suffix:
            return txt_path.stem.replace("_", "-")
        else:
            raise Alto2txtPathError(
                f"`txt_path` must be a full `ITEM` path, " f"got: '{txt_path}'"
            )
    else:
        path: Path = txt_path.parent
        if (
            start_year < int(path.parts[-2]) < final_year
            and int(path.parts[-1]) <= max_month_day_int
        ):
            path = Path(*(path.parts[:-2] + ("".join(path.parts[-2:]),)))
        path = Path(*path.parts[: type + 1])
        return str(path).replace("/", "-")
