"""http exceptions"""


class HTTPException(Exception):
    """add http attributes to base exception"""

    def __init__(self, code, reason, explanation=""):
        super(HTTPException).__init__()
        self.code = code
        self.reason = reason
        self.explanation = explanation


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


class RequiredAttributeError(AttributeError):
    """missing attribute in http payload"""

    def __init__(self, name):
        self.args = (f"missing required attribute: {name}",)
