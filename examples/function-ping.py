"""ping/pong using a local function"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__package__)


def ping():
    log.info("in the ping function")
    return "pong"


if __name__ == "__main__":  # allow module to be imported without running
    web.add_server().add_route("/ping", ping)
    web.run()
