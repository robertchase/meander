"""tests to lock down connection request handling"""

import asyncio

from meander import Request
from meander.connection import Connection
from meander.router import Endpoint


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

    def __init__(self, handler, args=None, before=None, after=None):
        self.handler = handler
        self.args = [] if not args else args
        self.before = [] if not before else before
        self.after = [] if not after else after

    def __call__(self, *args):
        return Endpoint(self.handler, self.args, False, self.before, self.after)


def test_text():
    """simple text return"""

    def handler():
        return "abc"

    writer = ByteWriter()
    con = Connection(None, writer, EasyRouter(handler))

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith(bytes("\r\nabc", "utf-8"))

    asyncio.run(test())


def test_text_coro():
    """simple text return from coroutine"""

    async def handler():
        return "abc"

    writer = ByteWriter()
    con = Connection(None, writer, EasyRouter(handler))

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith(bytes("\r\nabc", "utf-8"))

    asyncio.run(test())


def test_none():
    """simple None return"""

    def handler():
        return None

    writer = ByteWriter()
    con = Connection(None, writer, EasyRouter(handler))

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith(bytes("\r\nContent-Length: 0\r\n\r\n", "utf-8"))

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
        assert writer.out.endswith(bytes('\r\n{"a": 1, "b": 2}', "utf-8"))

    asyncio.run(test())


def test_after():
    """after hook transforms result"""

    def handler():
        return "original"

    def after_hook(request, result):
        return result.upper()

    writer = ByteWriter()
    con = Connection(None, writer, EasyRouter(handler, after=[after_hook]))

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith(b"\r\nORIGINAL")

    asyncio.run(test())


def test_after_coro():
    """async after hook transforms result"""

    def handler():
        return "hello"

    async def after_hook(request, result):
        return result + " world"

    writer = ByteWriter()
    con = Connection(None, writer, EasyRouter(handler, after=[after_hook]))

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith(b"\r\nhello world")

    asyncio.run(test())


def test_after_none_keeps_result():
    """after hook returning None does not replace result"""

    def handler():
        return "keep me"

    def after_hook(request, result):
        pass  # returns None implicitly

    writer = ByteWriter()
    con = Connection(None, writer, EasyRouter(handler, after=[after_hook]))

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith(b"\r\nkeep me")

    asyncio.run(test())


def test_before_and_after():
    """before and after hooks on same route"""

    def before_hook(request):
        request.content = {"value": 10}

    def after_hook(request, result):
        return result * 2

    def handler(content):
        return content["value"]

    writer = ByteWriter()
    con = Connection(
        None,
        writer,
        EasyRouter(handler, before=[before_hook], after=[after_hook]),
    )

    async def test():
        await con.handle_request(Request())
        assert writer.out.endswith(b"\r\n20")

    asyncio.run(test())
