import logging

import meander as web


logging.basicConfig(level=logging.DEBUG)


def first(request):
    if value := request.http_headers.get("first"):
        request.content["first"] = value


def ping():
    return "pong"


def echo(request: web.Request):
    return request.content


def add(a: int, b: int = 1, first: str = "", con_id: web.ConnectionId = "") -> int:
    print(f"{con_id=} {first=}")
    return a + b


web.add_server({
    "/ping": ping,
    "/echo": {
        "GET": echo,
        "PUT": echo,
    },
    "/add": {
        "GET": {
            "prelude": [first],
            "handler": add,
        }
    },
})
web.run()
