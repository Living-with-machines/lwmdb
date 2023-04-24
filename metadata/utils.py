from typing import Final, Sequence

VALID_TRUE_STRS: Final[tuple[str, ...]] = ("y", "yes", "t", "true", "on", "1")
VALID_FALSE_STRS: Final[tuple[str, ...]] = ("n", "no", "f", "false", "off", "0")


def str_to_bool(
    val: str,
    true_strs: Sequence[str] = VALID_TRUE_STRS,
    false_strs: Sequence[str] = VALID_FALSE_STRS,
) -> bool:
    """Convert values of `true_strs` to True and `false_strs` to False.

    See
    https://docs.python.org/3/distutils/apiref.html#distutils.util.strtobool
    which is due to depricate, hence equivalent below.
    """
    if val.lower() in true_strs:
        return True
    elif val.lower() in false_strs:
        return False
    else:
        raise ValueError(
            f"{val} dose not match True values: {true_strs} "
            f"or False values {false_strs}"
        )
