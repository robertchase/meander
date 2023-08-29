"""tests to lock down connection request handling"""
import asyncio

from meander import Request
from meander.connection import Connection
from meander.router import Route


class ByteWriter:
    """mock write stream"""

    def __init__(self):
        self.out = b""

    def write(self, value: bytes):
        """append value to buffer"""
        self.out += value

    def get_extra_info(self, *args):  # pylint: disable=unused-argument
        """return dummy value"""
        return ["", ""]


class EasyRouter:  # pylint: disable=too-few-public-methods
    """always returns the same thing (not testing routing function)"""

    def __init__(self, handler, args=None, before=None):
        self.handler = handler
        self.args = [] if not args else args
        self.before = [] if not before else before

    def __call__(self, *args):
        return Route(self.handler, self.args, False, self.before)


def test_text():
    """simple text return"""

    def handler():
        return "abc"

    writer = ByteWriter()
    con = Connection(None, writer, EasyRouter(handler))

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith("\r\nabc".encode())

    asyncio.run(test())


def test_text_coro():
    """simple text return from coroutine"""

    async def handler():
        return "abc"

    writer = ByteWriter()
    con = Connection(None, writer, EasyRouter(handler))

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith("\r\nabc".encode())

    asyncio.run(test())


def test_none():
    """simple None return"""

    def handler():
        return None

    writer = ByteWriter()
    con = Connection(None, writer, EasyRouter(handler))

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith("\r\nContent-Length: 0\r\n\r\n".encode())

    asyncio.run(test())


def test_args():
    """args handling"""

    arg1 = "abc"
    arg2 = "def"

    def handler(first, second):
        return f"{first}-{second}"

    writer = ByteWriter()
    con = Connection(None, writer, EasyRouter(handler, args=[arg1, arg2]))

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith(f"\r\n{arg1}-{arg2}".encode())

    asyncio.run(test())


def test_before():
    """before handling"""

    def before_1(request):
        request.content = {"a": 1}

    async def before_2(request):
        request.content["b"] = 2

    def handler(content):
        return content

    writer = ByteWriter()
    con = Connection(None, writer, EasyRouter(handler, before=[before_1, before_2]))

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith('\r\n{"a": 1, "b": 2}'.encode())

    asyncio.run(test())
