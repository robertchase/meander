"""tests for types"""
import pytest

from meander import types


@pytest.mark.parametrize(
    "value, is_valid, result",
    (
        (1, True, True),
        ("1", True, True),
        (True, True, True),
        ("true", True, True),
        ("TrUe", True, True),
        (2, False, None),
        (0, True, False),
        ("0", True, False),
        (False, True, False),
        ("false", True, False),
        ("FALse", True, False),
    ),
)
def test_boolean(value, is_valid, result):
    """test boolean operation"""
    if is_valid:
        assert types.boolean(value) == result
    else:
        with pytest.raises(ValueError):
            types.boolean(value)


@pytest.mark.parametrize(
    "value, is_valid, result",
    (
        (1, True, 1),
        ("1", True, 1),
        (0, True, 0),
        (True, False, None),
        ("1a", False, None),
        (None, False, None),
        ("abc", False, None),
    ),
)
def test_integer(value, is_valid, result):
    """test integer operation"""
    if is_valid:
        assert types.integer(value) == result
    else:
        with pytest.raises(ValueError):
            types.integer(value)


def test_string_ctor():
    """test String construction"""

    with pytest.raises(AttributeError):
        types.String(min_length=-1)

    with pytest.raises(AttributeError):
        types.String(min_length=5, max_length=3)


@pytest.mark.parametrize(
    "min_length,max_length,value,is_valid,result",
    (
        (0, None, "abc", True, "abc"),
        (0, None, 100, True, "100"),
        (0, None, None, True, "None"),
        (0, None, True, True, "True"),
        (0, None, False, True, "False"),
        (3, 3, "abc", True, "abc"),
        (0, 3, "abcde", False, None),
        (3, 5, "a", False, None),
    ),
)
def test_string(min_length, max_length, value, is_valid, result):
    """test String operation"""
    validator = types.String(min_length, max_length)
    if is_valid:
        assert validator(value) == result
    else:
        with pytest.raises(ValueError):
            validator(value)
