"""GET+PUT /echo"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)


def echo(request):
    return request.content


web.add_server({
    "/ping": "pong",
    "/echo": {
        "GET": echo,
        "PUT": echo,
    },
})
web.run()
