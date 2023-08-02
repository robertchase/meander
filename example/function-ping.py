"""ping/pong using a local function"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__package__)


def ping():
    log.info("in the ping function")
    return "pong"


web.add_server({"/ping": ping})
web.run()
