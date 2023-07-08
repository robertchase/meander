"""parser for http documents"""
import asyncio
import gzip
import json
import re
import urllib.parse as urlparse

from meander.exception import HTTPException, HTTPEOF
from meander.request import Request


class HTTPReader:  # pylint: disable=too-many-instance-attributes
    """stream reader that supports a max line length and timeout

       if multiple http documents are expected to arrive on the same
       connection, then wrapping the stream reader before calling the parse
       function allows the buffering (read_block) to work properly.

       Notes:
           1. the connection will remain open for "timeout" seconds while
              waiting for a new document to arrive
           2. if a document has been partially read, then the connection will
              remain open for "active_timeout" seconds while waiting for
              additional data to arrive
           3. each read will grab no more than "max_read_size" bytes from
              the connection, allowing for equitable use of network resources
              between connections
    """

    def __init__(self,  # pylint: disable=too-many-arguments
                 reader, max_line_length=10_000, max_header_count=100,
                 max_content_length=None, timeout=60, active_timeout=5,
                 max_read_size=5000, is_server=True):
        self.reader = reader
        self.max_line_length = max_line_length
        self.max_header_count = max_header_count
        self.max_content_length = max_content_length
        self.timeout = timeout  # time to wait for initial data (empty buffer)
        self.active_timeout = active_timeout  # time to wait for more data
        self.max_read_size = max_read_size
        self.is_server = is_server
        self.buffer = b""

    async def read_block(self):
        """read a block from the underlying stream"""

        async def _read():
            return await self.reader.read(self.max_read_size)

        if len(self.buffer):
            timeout = self.active_timeout
        else:
            timeout = self.timeout
        data = await asyncio.wait_for(_read(), timeout)

        if len(data) == 0:
            raise HTTPEOF()

        self.buffer += data

    async def read(self, length):
        """read length bytes"""
        while True:
            if len(self.buffer) >= length:
                data, self.buffer = self.buffer[:length], self.buffer[length:]
                return data
            await self.read_block()

    async def readline(self):
        """read a line (ends in \n or \r\n) as ascii"""
        while True:
            test = self.buffer.split(b"\n", 1)
            if len(test) == 2:
                line, self.buffer = test
                if line.endswith(b"\r"):
                    line = line[:-1]
                if len(line) > self.max_line_length:
                    raise HTTPException(431, "Request Header Fields Too Long")
                return line.decode("ascii")

            if len(self.buffer) > self.max_line_length:
                raise HTTPException(431, "Request Header Fields Too Long",
                                    "no end of line encountered")
            await self.read_block()

    async def read_document(self):
        """read the next document from the reader"""
        return await parse(self)


async def parse(reader):
    """parse an HTTP document from a stream"""

    if not isinstance(reader, HTTPReader):
        reader = HTTPReader(reader)

    document = Request()

    try:
        if reader.is_server:
            await parse_server(reader, document)
        else:
            await parse_client(reader, document)
    except HTTPEOF:
        document = None

    return document


async def parse_server(reader, document):
    """parse a server document from reader"""

    # --- status: <method> <resource> HTTP/1.1
    status = await reader.readline()
    toks = status.split()

    if len(toks) != 3:
        raise HTTPException(400, "Bad Request", "malformed status line")

    if toks[2] != "HTTP/1.1":
        raise HTTPException(400, "Bad Request",
                            f"unsupported HTTP protocol: {toks[2]}")

    document.http_method = toks[0].upper()
    res = urlparse.urlparse(toks[1])
    document.http_resource = res.path
    if res.query:
        document.http_query_string = res.query
        for key, val in urlparse.parse_qs(res.query).items():
            document.http_query[key] = val[0] if len(val) == 1 else val

    await parse_headers_and_body(reader, document)

    if document.http_method == "GET":
        document.content = document.http_query
    elif document.http_method in ("PATCH", "POST", "PUT"):
        parse_content(document)


async def parse_client(reader, document):
    """parse a client document from reader"""

    # --- status: HTTP/1.1 <code> [<message>]
    status = await reader.readline()
    toks = status.split()

    if len(toks) == 1:
        raise HTTPException(400, "Bad Request", "malformed status line")

    if toks[0] != "HTTP/1.1":
        raise HTTPException(400, "Bad Request",
                            f"unsupported HTTP protocol: {toks[0]}")

    try:
        document.http_status_code = int(toks[1])
    except ValueError as exc:
        raise HTTPException(
            400, "Bad Request", f"invalid status code: {toks[1]}") from exc

    if len(toks) == 2:
        document.http_status_message = ""
    else:
        document.http_status_message = " ".join(toks[2:])

    await parse_headers_and_body(reader, document)

    parse_content(document)


async def parse_headers_and_body(  # pylint: disable=too-many-branches
        reader, document):
    """parse headers and body from reader into document"""

    # --- headers
    while len(header := await reader.readline()) > 0:
        if len(document.http_headers) == reader.max_header_count:
            raise HTTPException(400, "Bad Request",
                                "max header count exceeded")
        test = header.split(":", 1)
        if len(test) != 2:
            raise HTTPException(400, "Bad Request", "header missing colon")
        name, value = test
        document.http_headers[name.strip().lower()] = value.strip()

    # --- keep alive
    keep_alive = document.http_headers.get("connection", "keep-alive")
    document.is_keep_alive = keep_alive == "keep-alive"

    # --- http content
    await parse_http_content(reader, document)

    # --- content type
    if "content-type" in document.http_headers and \
            document.http_headers.get("content-type") == "":
        raise HTTPException(400, "Bad Request",
                            "invalid content-type header")

    content_type = document.http_headers.get("content-type")
    if content_type:

        # lenient content-type parser
        pattern = (
            r"\s*"                 # optional leading spaces
            "(?P<type>.+?)"        # content type
            r"\s*/\s*"             # slash with optional spaces
            "(?P<subtype>[^;]+?)"  # content subtype
            "("                    # start of optional parameter specification
            r"\s*;\s*"             # semicolon with optional spaces
            "(?P<attribute>.+?)"   # attribute name
            r"\s*=\s*"             # equal with optional spaces
            "(?P<value>.+?)"       # attribute value
            ")?"                   # end of optional parameter specification
            r"\s*$"                # optional spaces and end of line
        )
        match = re.match(pattern, content_type)
        if not match:
            raise HTTPException(400, "Bad Request",
                                "invalid content-type header")
        ctype = match.groupdict()
        document.http_content_type = f"{ctype['type']}/{ctype['subtype']}"
        if ctype.get("attribute") == "charset":
            document.http_charset = ctype["value"]

    # --- content encoding
    encoding = document.http_headers.get("content-encoding")
    if encoding:
        if encoding != "gzip":
            raise HTTPException(400, "Bad Request",
                                "unsupported content encoding")
    document.http_encoding = encoding

    # --- compress
    if document.http_content and document.http_encoding == "gzip":
        try:
            data = gzip.decompress(document.http_content)
        except Exception as exc:
            raise HTTPException(
                400, "Bad Request", "malformed gzip data") from exc
        document.http_content = data.decode(document.http_charset or "utf-8")


async def parse_http_content(reader, document):
    """parse the http body from reader"""

    if document.http_headers.get("transfer-encoding") == "chunked":
        return await parse_chunked(reader, document)

    length = document.http_headers.get("content-length")
    if length is None:
        length = 0

    try:
        document.http_content_length = int(length)
    except ValueError as exc:
        raise HTTPException(
            400, "Bad Request", "invalid content-length") from exc

    if reader.max_content_length:
        if document.http_content_length > reader.max_content_length:
            raise HTTPException(413, "Request Entity Too Large")

    if document.http_content_length:
        document.http_content = await reader.read(document.http_content_length)


async def parse_chunked(reader, document):
    """parse chunked data from reader"""
    document.http_content = b""
    while True:
        line = await reader.readline()
        line = line.split(";", 1)[0]  # sometimes there are semicolons
        try:
            length = int(line, 16)
        except ValueError as exc:
            raise Exception(
                f"Invalid transfer-encoding chunk length: {line}") from exc
        if length == 0:
            break
        document.http_content += await reader.read(length)


def parse_content(document):
    """extract content based on http_content_type"""
    if document.http_content_type == "application/json":
        try:
            document.content = json.loads(document.http_content)
        except json.decoder.JSONDecodeError as exc:
            raise HTTPException(400, "Bad Request", "invalid json content") \
                from exc
    elif document.http_content_type == "application/x-www-form-urlencoded":
        if document.http_content:
            query = urlparse.parse_qs(document.http_content.decode("ascii"),
                                      keep_blank_values=True)
            document.content = {
                n: v[0] if len(v) == 1 else v for n, v in query.items()
            }
    elif document.http_content_type == "text/plain":
        if document.http_content is None:
            document.content = ""
        else:
            document.content = document.http_content.decode()
    else:
        document.content = document.http_content
