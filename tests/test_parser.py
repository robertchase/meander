"""tests for http parser"""
import asyncio
import gzip
import json

import pytest

from meander.exception import HTTPException, HTTPEOF
from meander.parser import HTTPReader, parse


class ByteReader:  # pylint: disable=too-few-public-methods
    """mock read stream"""

    def __init__(self, data, sleep=None):
        self.data = data
        self.sleep = sleep

    async def read(self, length):
        """return length bytes from self.data"""
        if self.sleep:
            await asyncio.sleep(self.sleep)
        result, self.data = self.data[:length], self.data[length:]
        return result


def test_reader_read():
    """test reader read method"""
    reader = HTTPReader(ByteReader(b"12345678"))

    async def test():
        assert b"1234" == await reader.read(4)
        assert b"567" == await reader.read(3)
        with pytest.raises(HTTPEOF):
            await reader.read(10)

    asyncio.run(test())


def test_reader_readline():
    """test reader readline method"""
    reader = HTTPReader(ByteReader(b"one\ntwo\r\nthree"))

    async def test():
        assert "one" == await reader.readline()
        assert "two" == await reader.readline()
        with pytest.raises(HTTPEOF):
            await reader.readline()

    asyncio.run(test())


@pytest.mark.parametrize(
    "max_length, data",
    (
        (10, b"123456789012345"),
        (10, b"12345678901\r\n2345"),
    ),
)
def test_reader_max_line_length(max_length, data):
    """test max line length"""
    reader = HTTPReader(ByteReader(data), max_length)

    async def test():
        with pytest.raises(HTTPException):
            await reader.readline()

    asyncio.run(test())


def test_reader_timeout():
    """test read timeout"""
    reader = HTTPReader(ByteReader(b"abc", sleep=0.01), timeout=0.001)

    async def test():
        with pytest.raises(asyncio.TimeoutError):
            await reader.readline()

    asyncio.run(test())


@pytest.mark.parametrize(
    "data, message",
    (
        (b"POST\n", "malformed status line"),
        (b"POST /\n", "malformed status line"),
        (b"POST / HTTP/1.2\n", "unsupported HTTP protocol: HTTP/1.2"),
    ),
)
def test_bad_status(data, message):
    """test bad status lines"""
    reader = HTTPReader(ByteReader(data))

    async def test():
        with pytest.raises(HTTPException) as exc:
            await parse(reader)
        assert exc.value.args[2] == message

    asyncio.run(test())


@pytest.mark.parametrize(
    "data, message",
    (
        (b"HTTP/1.1\n", "malformed status line"),
        (b"AKK 200\n", "unsupported HTTP protocol: AKK"),
        (b"HTTP/1.1 ABC\n", "invalid status code: ABC"),
    ),
)
def test_bad_client_status(data, message):
    """test bad client status lines"""
    reader = HTTPReader(ByteReader(data), is_server=False)

    async def test():
        with pytest.raises(HTTPException) as exc:
            await parse(reader)
        assert exc.value.args[2] == message

    asyncio.run(test())


def test_status():
    """test good status line"""
    reader = HTTPReader(ByteReader(b"POST / HTTP/1.1\n\n"))

    async def test():
        await parse(reader)

    asyncio.run(test())


@pytest.mark.parametrize(
    "data, code, message",
    (
        (b"HTTP/1.1 200\n\n", 200, ""),
        (b"HTTP/1.1 400 Bad Request\n\n", 400, "Bad Request"),
    ),
)
def test_client_status(data, code, message):
    """test client status lines"""
    reader = HTTPReader(ByteReader(data), is_server=False)

    async def test():
        document = await parse(reader)
        assert document.http_status_code == code
        assert document.http_status_message == message

    asyncio.run(test())


@pytest.mark.parametrize(
    "data, count, message",
    (
        (b"POST / HTTP/1.1\none:1\ntwo:2\n\n", 1, "max header count exceeded"),
        (b"POST / HTTP/1.1\none:1\ntwo2\n\n", 100, "header missing colon"),
    ),
)
def test_bad_header(data, count, message):
    """test bad headers"""
    reader = HTTPReader(ByteReader(data), max_header_count=count)

    async def test():
        with pytest.raises(HTTPException) as exc:
            await parse(reader)
        assert exc.value.args[2] == message

    asyncio.run(test())


def test_header():
    """test good header"""
    reader = HTTPReader(ByteReader(b"POST / HTTP/1.1\none:1\ntwo:2\n\n"))

    async def test():
        document = await parse(reader)
        assert document.http_headers["one"] == "1"

    asyncio.run(test())


@pytest.mark.parametrize(
    "data, flag",
    (
        (b"POST / HTTP/1.1\nconnection: close\n\n", False),
        (b"POST / HTTP/1.1\nnothing: to see\n\n", True),
        (b"POST / HTTP/1.1\nconnection: keep-alive\n\n", True),
    ),
)
def test_keep_alive_flag(data, flag):
    """test keep-alive header"""
    reader = HTTPReader(ByteReader(data))

    async def test():
        document = await parse(reader)
        assert document.is_keep_alive is flag

    asyncio.run(test())


def test_bad_content_length():
    """test bad content length"""
    reader = HTTPReader(ByteReader(b"POST / HTTP/1.1\ncontent-length: akk\n\n"))

    async def test():
        with pytest.raises(HTTPException) as exc:
            await parse(reader)
        assert exc.value.args[2] == "invalid content-length"

    asyncio.run(test())


def test_content_length_too_long():
    """test content length too long"""
    reader = HTTPReader(
        ByteReader(b"POST / HTTP/1.1\ncontent-length: 100\n\n"), max_content_length=10
    )

    async def test():
        with pytest.raises(HTTPException) as exc:
            await parse(reader)
        assert exc.value.args[0] == 413
        assert exc.value.args[1] == "Request Entity Too Large"

    asyncio.run(test())


@pytest.mark.parametrize(
    "data, length",
    (
        (b"POST / HTTP/1.1\nnothing: to see\n\n", 0),
        (b"POST / HTTP/1.1\ncontent-length: 0\n\n", 0),
        (b"POST / HTTP/1.1\ncontent-length: 5\n\n12345", 5),
    ),
)
def test_content_length(data, length):
    """test keep-alive header"""
    reader = HTTPReader(ByteReader(data))

    async def test():
        document = await parse(reader)
        assert document.http_content_length == length

    asyncio.run(test())


@pytest.mark.parametrize(
    "data",
    (
        b"POST / HTTP/1.1\nContent-Type:\n\n",
        b"POST / HTTP/1.1\nContent-Type: text\n\n",
        b"POST / HTTP/1.1\nContent-Type: text/\n\n",
        b"POST / HTTP/1.1\nContent-Type: text/plain;\n\n",
        b"POST / HTTP/1.1\nContent-Type: text/plain;foo\n\n",
        b"POST / HTTP/1.1\nContent-Type: text/plain;foo=\n\n",
    ),
)
def test_bad_content_type(data):
    """test content-type header"""
    reader = HTTPReader(ByteReader(data))

    async def test():
        with pytest.raises(HTTPException) as exc:
            await parse(reader)
        assert exc.value.args[2] == "invalid content-type header"

    asyncio.run(test())


@pytest.mark.parametrize(
    "data, result, charset",
    (
        (b"POST / HTTP/1.1\nContent-Type: text/plain\n\n", "text/plain", None),
        (
            b"POST / HTTP/1.1\nContent-Type: text/plain;charset=foo\n\n",
            "text/plain",
            "foo",
        ),
        (b"POST / HTTP/1.1\nContent-Type: text/plain;foo=bar\n\n", "text/plain", None),
    ),
)
def test_content_type(data, result, charset):
    """test content-type header"""
    reader = HTTPReader(ByteReader(data))

    async def test():
        document = await parse(reader)
        assert document.http_content_type == result
        assert document.http_charset == charset

    asyncio.run(test())


def test_bad_content_encoding():
    """test bad content encoding header"""
    reader = HTTPReader(ByteReader(b"POST / HTTP/1.1\ncontent-encoding:bad\n\n"))

    async def test():
        with pytest.raises(HTTPException) as exc:
            await parse(reader)
        assert exc.value.args[2] == "unsupported content encoding"

    asyncio.run(test())


def test_content_encoding():
    """test content encoding header"""
    reader = HTTPReader(ByteReader(b"POST / HTTP/1.1\ncontent-encoding:gzip\n\n"))

    async def test():
        document = await parse(reader)
        assert document.http_encoding == "gzip"

    asyncio.run(test())


def test_http_content():
    """test message body"""
    reader = HTTPReader(ByteReader(b"POST / HTTP/1.1\nContent-Length: 5\n\nabCDeF"))

    async def test():
        document = await parse(reader)
        assert document.http_content == b"abCDe"

    asyncio.run(test())


def test_gzip_http_content():
    """test gzipped message body"""
    body = gzip.compress(b"Abc123")
    stream = (
        "POST / HTTP/1.1\n"
        f"Content-Length: {len(body)}\n"
        "Content-Encoding: gzip\n\n"
    ).encode() + body
    reader = HTTPReader(ByteReader(stream))

    async def test():
        document = await parse(reader)
        assert document.http_content == "Abc123"

    asyncio.run(test())


def test_content_get():
    """test http_query handling"""
    reader = HTTPReader(ByteReader(b"GET /yeah?a=1&b=2 HTTP/1.1\n\n"))

    async def test():
        document = await parse(reader)
        assert document.http_resource == "/yeah"
        assert document.content["a"] == "1"
        assert document.content["b"] == "2"

    asyncio.run(test())


def test_content_bad_json():
    """test bad application/json handling"""
    body = b'{"bad":'
    data = (
        "PATCH / HTTP/1.1\n"
        "Content-Type: application/json\n"
        f"Content-Length: {len(body)}\n\n"
    ).encode() + body
    reader = HTTPReader(ByteReader(data))

    async def test():
        with pytest.raises(HTTPException) as exc:
            await parse(reader)
        assert exc.value.args[2] == "invalid json content"

    asyncio.run(test())


def test_content_json():
    """test application/json handling"""
    body = json.dumps({"a": 1, "b": 2}).encode()
    data = (
        "PATCH / HTTP/1.1\n"
        "Content-Type: application/json\n"
        f"Content-Length: {len(body)}\n\n"
    ).encode() + body
    reader = HTTPReader(ByteReader(data))

    async def test():
        document = await parse(reader)
        assert document.content["a"] == 1
        assert document.content["b"] == 2

    asyncio.run(test())


def test_content_form():
    """test application/x-www-form-urlencoded handling"""
    body = b"a=1&b=2"
    data = (
        "PATCH / HTTP/1.1\n"
        "Content-Type: application/x-www-form-urlencoded\n"
        f"Content-Length: {len(body)}\n\n"
    ).encode() + body
    reader = HTTPReader(ByteReader(data))

    async def test():
        document = await parse(reader)
        assert document.content["a"] == "1"
        assert document.content["b"] == "2"

    asyncio.run(test())
