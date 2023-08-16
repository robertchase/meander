"""ping/pong with non-logging handler"""
import logging

import meander as web


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__package__)


web.add_server({"/ping": {
        "GET": {
            "handler": "example.function-ping.ping",
            "silent": True,
        },
    },
})
web.run()
