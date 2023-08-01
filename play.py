import logging

import meander as web


logging.basicConfig(level=logging.DEBUG)


def echo(a: int, b: web.types.String(min_length=3, max_length=5)) -> dict:
    return dict(a=a, b=b)


async def pingping(request):
    result = await web.call("http://localhost:8080/ping")
    return result.content


def akk(a: str, b: str, **c):
    return dict(a=a, b=b, c=c)


web.add_server({
    "/akk": akk,
    "/ping": "pong",
    "/pingping": pingping,
    "/echo": {
        "GET": echo,
        "PUT": echo
    },
    r"/echo/(\d+)": echo,
})
web.run()
