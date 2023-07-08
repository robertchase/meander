import re


def boolean(value):
    if value in (1, "1", True):
        return True
    if value in (0, "0", False):
        return False
    raise ValueError("not a boolean")


def integer(value):
    if not re.match(r"\d+$", str(value)):
        raise ValueError("not an integer")
    return int(value)


class String:
    def __init__(self, min=0, max=None):
        self.min = int(min)
        if max:
            max = int(max)
            if max < min:
                raise AttributeError(f"max must be greater than {self.min}")
        self.max = max

    def __call__(self, value):
        value = str(value)
        if self.min:
            if len(value) < self.min:
                raise ValueError(f"length is less than minimum ({self.min})")
        if self.max:
            if len(value) > self.max:
                raise ValueError(f"length is more than maximum ({self.max})")
        return value
