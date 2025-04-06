"""ping/pong with non-logging handler"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__package__)


web.add_server().add_route("/ping", "examples.function-ping.ping", silent=True)
web.run()
