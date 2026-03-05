"""tests for http client"""

import asyncio

import pytest

from meander.client import Client
from meander.formatter import HTTPFormat


class MockWriter:
    """mock asyncio.StreamWriter"""

    def __init__(self):
        self.data = b""
        self.closed = False

    def write(self, data: bytes):
        """capture written data"""
        self.data += data

    def close(self):
        """mark as closed"""
        self.closed = True

    async def wait_closed(self):
        """no-op"""


class ByteReader:
    """mock asyncio.StreamReader that returns data in chunks"""

    def __init__(self, data: bytes):
        self.data = data

    async def read(self, length: int) -> bytes:
        """return up to length bytes"""
        result, self.data = self.data[:length], self.data[length:]
        return result


def _build_response(code=200, message="OK", body="", headers=None):
    """build a raw HTTP response byte string"""
    headers = headers or {}
    if body:
        headers["Content-Length"] = str(len(body))
    header_lines = "\r\n".join(f"{k}: {v}" for k, v in headers.items())
    head = f"HTTP/1.1 {code} {message}\r\n{header_lines}\r\n\r\n"
    return head.encode("ascii") + body.encode("utf-8")


def _make_client(response_data: bytes) -> tuple[Client, MockWriter]:
    """create a Client with mocked reader/writer, already 'opened'"""
    from meander.parser import HTTPReader

    client = Client()
    client.host = "example.com"
    client.writer = MockWriter()
    client.reader = HTTPReader(ByteReader(response_data), is_server=False)
    return client, client.writer


def test_write_default_get():
    """test write produces a valid GET request"""
    client, writer = _make_client(b"")
    payload = client.write()

    assert isinstance(payload, HTTPFormat)
    assert b"GET / HTTP/1.1" in writer.data


def test_write_post_with_content():
    """test write produces a POST with json content"""
    client, writer = _make_client(b"")
    client.write(
        method="POST",
        path="/api/data",
        content={"key": "value"},
        content_type="application/json",
    )

    assert b"POST /api/data HTTP/1.1" in writer.data
    assert b'"key": "value"' in writer.data


def test_write_with_bearer():
    """test write adds Authorization header for bearer token"""
    client, writer = _make_client(b"")
    client.write(bearer="my-token")

    assert b"Authorization: Bearer my-token" in writer.data


def test_write_with_bearer_preserves_headers():
    """test write adds bearer to existing headers"""
    client, writer = _make_client(b"")
    client.write(bearer="tok", headers={"X-Custom": "val"})

    assert b"Authorization: Bearer tok" in writer.data
    assert b"X-Custom: val" in writer.data


def test_write_with_close():
    """test write adds Connection: close header"""
    client, writer = _make_client(b"")
    client.write(close=True)

    assert b"Connection: close" in writer.data


def test_write_returns_payload():
    """test write returns the HTTPFormat payload"""
    client, _ = _make_client(b"")
    payload = client.write(method="PUT", path="/resource")

    assert isinstance(payload, HTTPFormat)
    assert payload.method == "PUT"
    assert payload.path == "/resource"


def test_read_parses_response():
    """test read returns a parsed ClientDocument"""
    response = _build_response(200, "OK", "hello")
    client, _ = _make_client(response)

    async def test():
        doc = await client.read()
        assert doc.http_status_code == 200
        assert doc.http_status_message == "OK"
        assert doc.http_content == b"hello"

    asyncio.run(test())


def test_read_updates_reader_settings():
    """test read passes timeout settings to reader"""
    response = _build_response(204, "No Content")
    client, _ = _make_client(response)

    async def test():
        await client.read(timeout=30, active_timeout=10, max_read_size=1000)
        assert client.reader.timeout == 30
        assert client.reader.active_timeout == 10
        assert client.reader.max_read_size == 1000

    asyncio.run(test())


def test_close():
    """test close calls writer close and wait_closed"""
    response = _build_response()
    client, writer = _make_client(response)

    async def test():
        await client.close()
        assert writer.closed

    asyncio.run(test())


def test_open_sets_host():
    """test open stores host and creates reader"""

    async def test():
        reader = ByteReader(b"")
        writer = MockWriter()

        with pytest.MonkeyPatch.context() as mp:

            async def mock_open_connection(host, port, ssl=None):
                return reader, writer

            mp.setattr(asyncio, "open_connection", mock_open_connection)

            client = Client()
            await client.open("localhost", 8080)
            assert client.host == "localhost"
            assert client.reader is not None
            assert client.reader.is_server is False

    asyncio.run(test())


def test_open_ssl_creates_context():
    """test open with is_ssl=True creates an SSL context"""
    contexts_created = []

    async def test():
        reader = ByteReader(b"")
        writer = MockWriter()

        with pytest.MonkeyPatch.context() as mp:

            async def mock_open_connection(host, port, ssl=None):
                contexts_created.append(ssl)
                return reader, writer

            mp.setattr(asyncio, "open_connection", mock_open_connection)

            client = Client()
            await client.open("example.com", 443, is_ssl=True)

    asyncio.run(test())
    assert len(contexts_created) == 1
    assert contexts_created[0] is not None


def test_open_no_ssl_passes_none():
    """test open with is_ssl=False passes ssl=None"""
    ssl_args = []

    async def test():
        reader = ByteReader(b"")
        writer = MockWriter()

        with pytest.MonkeyPatch.context() as mp:

            async def mock_open_connection(host, port, ssl=None):
                ssl_args.append(ssl)
                return reader, writer

            mp.setattr(asyncio, "open_connection", mock_open_connection)

            client = Client()
            await client.open("example.com", 80, is_ssl=False)

    asyncio.run(test())
    assert ssl_args == [None]
