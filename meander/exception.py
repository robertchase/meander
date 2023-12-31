"""http exceptions"""


class HTTPException(Exception):
    """add http attributes to base exception"""

    def __init__(self, code, reason, explanation=""):
        super(HTTPException).__init__()
        self.code = code
        self.reason = reason
        self.explanation = explanation


class HTTPBadRequest(HTTPException):
    """helper class for '400 Bad Request exception"""

    def __init__(self, explanation=""):
        super().__init__(400, "Bad Request", explanation)


class HTTPEOF(Exception):
    """end of stream before full document is read"""


class ExtraAttributeError(AttributeError):
    """extra attributes in http payload"""

    def __init__(self, name):
        self.args = (f"extra attribute(s): {', '.join(name)}",)


class DuplicateAttributeError(AttributeError):
    """duplicate attribute in http payload"""

    def __init__(self, name):
        self.args = (f"duplicate attribute: {name}",)


class PayloadValueError(ValueError):
    """invalid value in payload"""

    def __init__(self, name, err):
        self.args = (f"invalid {name} value: {err}",)


class RequiredAttributeError(AttributeError):
    """missing attribute in http payload"""

    def __init__(self, name):
        self.args = (f"missing required attribute: {name}",)
