import pytest

from ..utils import VALID_FALSE_STRS, VALID_TRUE_STRS, str_to_bool


@pytest.mark.parametrize("val", VALID_TRUE_STRS)
def test_str_to_bool_true(val):
    assert str_to_bool(val) == True
    assert str_to_bool(val.upper()) == True


@pytest.mark.parametrize("val", VALID_FALSE_STRS)
def test_str_to_bool_false(val):
    assert str_to_bool(val) == False
    assert str_to_bool(val.upper()) == False


def test_str_to_bool_true_invalid():
    with pytest.raises(ValueError):
        str_to_bool("Truue")
