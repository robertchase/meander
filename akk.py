from functools import wraps
import logging

import meander as web


logging.basicConfig(level=logging.DEBUG)


def first(request):
    if value := request.http_headers.get("first"):
        request.content["first"] = value


def add_arg(handler):
    @wraps(handler)
    def _add_arg(*args, **kwargs):
        kwargs["extra"] = "hi"
        return handler(*args, **kwargs)
    return _add_arg


class Reverse(web.ParamType):
    def __call__(cls, value):
        return str(value)[::-1]


def ping():
    return "pong"


def echo(request: web.Request):
    return request.content


def add(a: int, b: int = 1):
    return a + b


@add_arg
def play(a: Reverse, extra=""):
    return {"extra": extra, "a": a}


web.add_server({
    "/ping": ping,
    "/echo": {
        "GET": echo,
        "PUT": echo,
    },
    "/add": {
        "GET": {
            "before": [first],
            "handler": add,
        }
    },
    "/play": play,
})
web.run()
