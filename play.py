import logging

import meander as web


logging.basicConfig(level=logging.DEBUG)


async def ping(request):
    return "pong"


@web.payload(a=int, b=str)
async def echo(a, b):
    return dict(a=a, b=b)


web.add_server("test",
    {"/ping": {"GET": ping},
     "/echo": {"GET": echo, "PUT": echo},
     "/echo/(\d+)": {"GET": echo},
    }, 12345)
web.run()
