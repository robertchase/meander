class Request:  # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods
    """container for http document data"""

    def __init__(self):
        self.http_status_code = None  # client
        self.http_status_message = None  # client
        self.http_method = None  # server
        self.http_resource = None  # server
        self.http_query_string = ""  # server
        self.http_query = {}  # server

        self.http_headers = {}
        self.http_content_length = None
        self.http_content_type = None
        self.http_charset = None
        self.http_encoding = None
        self.http_content_type = None
        self.http_content = None
        self.is_keep_alive = True
        self.content = {}
