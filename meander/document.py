"""containers for parsed HTTP client and server documents"""


class Document:  # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods
    """container for http document data"""

    def __init__(self):
        self.http_headers = {}
        self.http_content_length = None
        self.http_content_type = None
        self.http_charset = None
        self.http_encoding = None
        self.http_content_type = None
        self.http_content = None
        self.is_keep_alive = True
        self.content = {}


# pylint: disable-next=too-few-public-methods,too-many-instance-attributes
class ServerDocument(Document):
    """container for server-side http document data"""

    def __init__(self):
        super().__init__()
        self.id = None  # pylint: disable=invalid-name
        self.connection_id = None
        self.http_method = None
        self.http_resource = None
        self.http_query_string = ""
        self.http_query = {}
        self.args = None  # re.Match.groups() from url


class ClientDocument(Document):  # pylint: disable=too-few-public-methods
    """container for client-side http document data"""

    def __init__(self):
        super().__init__()
        self.http_status_code = None
        self.http_status_message = None
