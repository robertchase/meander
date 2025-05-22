"""meander types"""

import re


ConnectionId = type("CONNECTIONID", (), {})
Ignore = type("IGNORE", (), {})


def boolean(value):
    """boolean type that accepts 1, "1", True, 0, "0", False"""
    if isinstance(value, str) and value.lower() == "true":
        return True
    if isinstance(value, str) and value.lower() == "false":
        return False
    if value in (1, "1", True):
        return True
    if value in (0, "0", False):
        return False
    raise ValueError("not a boolean")


def integer(value):
    """integer type that converts ints or strings of digits to int"""
    if not re.match(r"\d+$", str(value)):
        raise ValueError("not an integer")
    return int(value)


class String:  # pylint: disable=too-few-public-methods
    """string type with min and max length settings"""

    def __init__(self, min_length=0, max_length=None):
        self.min_length = int(min_length)
        if self.min_length < 0:
            raise AttributeError("min_length must be greater than or equal to zero")
        if max_length:
            max_length = int(max_length)
            if max_length < min_length:
                raise AttributeError(
                    f"max_length must be greater than {self.min_length}"
                )
        self.max_length = max_length

    def __call__(self, value):
        value = str(value)
        if self.min_length:
            if len(value) < self.min_length:
                raise ValueError(
                    f"is shorter than the minimum length ({self.min_length})"
                )
        if self.max_length:
            if len(value) > self.max_length:
                raise ValueError(
                    f"is longer than the maximum length ({self.max_length})"
                )
        return value
