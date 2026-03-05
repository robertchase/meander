"""http exceptions"""

from typing import Any


class HTTPException(Exception):
    """add http attributes to base exception"""

    def __init__(self, code: int, reason: str, explanation: str = "") -> None:
        super(HTTPException).__init__()
        self.code = code
        self.reason = reason
        self.explanation = explanation


class HTTPBadRequest(HTTPException):
    """helper class for '400 Bad Request exception"""

    def __init__(self, explanation: str = "") -> None:
        super().__init__(400, "Bad Request", explanation)


class HTTPEOF(Exception):
    """end of stream before full document is read"""


class ExtraAttributeError(AttributeError):
    """extra attributes in http payload"""

    def __init__(self, name: list[str]) -> None:
        self.args = (f"extra attribute(s): {', '.join(name)}",)


class DuplicateAttributeError(AttributeError):
    """duplicate attribute in http payload"""

    def __init__(self, name: str) -> None:
        self.args = (f"duplicate attribute: {name}",)


class PayloadValueError(ValueError):
    """invalid value in payload"""

    def __init__(self, name: str, err: Any) -> None:
        self.args = (f"invalid {name} value: {err}",)


class RequiredAttributeError(AttributeError):
    """missing attribute in http payload"""

    def __init__(self, name: str) -> None:
        self.args = (f"missing required attribute: {name}",)
