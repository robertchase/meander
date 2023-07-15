import logging

import meander as web


logging.basicConfig(level=logging.DEBUG)


async def ping(request):
    return "pong"


@web.payload(a=int, b=web.param.String(min=3, max=5))
async def echo(a, b):
    return dict(a=a, b=b)


web.add_server(
    "test", {
        "/ping": {"GET": ping},
        "/echo": {"GET": echo, "PUT": echo},
        r"/echo/(\d+)": {"GET": echo}
    },
    port=12345,
    ssl_certfile="tmp.com.crt", ssl_keyfile="tmp.com.key")
web.run()
