import logging

import meander as web


logging.basicConfig(level=logging.DEBUG)


@web.payload_noid(a=int, b=web.param.String(min=3, max=5))
def echo(a: int, b: str) -> dict:
    return dict(a=a, b=b)


async def pingping(request):
    result = await web.call("http://localhost:8080/ping")
    return result.content


@web.payload_noid(gather_extra_kwargs=True, a=str, b=str)
def akk(a, b, **c):
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
