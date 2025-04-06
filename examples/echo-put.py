"""GET+PUT /echo"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)


def echo(content):
    return content


(web.add_server()
    .add_route("/ping", "pong")
    .add_route("/echo", echo)
    .add_route("/echo", echo, method="PUT")
)
web.run()
