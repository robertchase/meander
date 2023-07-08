"""http exceptions"""


class HTTPException(Exception):
    """add http attributes to base exception"""

    def __init__(self, code, reason, explanation=''):
        super(HTTPException).__init__()
        self.code = code
        self.reason = reason
        self.explanation = explanation


class HTTPEOF(Exception):
    """end of stream before full document is read"""
