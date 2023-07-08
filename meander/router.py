"""simple router utility"""
from functools import namedtuple
import importlib
import re


Route = namedtuple("Route", "handler, args, silent")


class Router:

    def __init__(self, routes):
        """create a router for http requests

           "routes" is a dict of the form:
                {
                    "pattern": {
                        "method": "path",
                        "method": {"silent": True, "handler": "path"},...
                    },...
                }

            where:
                - "pattern" is a regex matching an http_resource
                - "method" is a string matching an http_method ("GET", "POST",
                  etc).
                - "path" is an http handler or a dot-delimited path to an http
                  handler.

            example:
                {
                    "/ping": {
                        "GET": "myapp.basic.ping",
                    },
                    "/user/([0-9a-f]{16})": {
                        "GET": "myapp.user.get_user",
                        "POST": "myapp.user.add_user",
                    },
                }

            the router instance is used like this:

                if route := router(http_resource, http_method):
                    # handle the http_document

            the returned route has three attributes:
                handler - callable that takes an http_document and returns
                          any result
                silent - a flag that controls the logging in aiohttp
                args - list of regex groups parsed from the http_resource
                       using the pattern

            Notes:

            1. the pattern must match the complete resource.
            2. the first pattern that matches the resource wins (so, when
               there is ambiguity, put more specific patterns first).
            3. if no pattern matches the resource, None is returned
            4. if grouping parethesis are used in pattern then the grouped
               items are returned in the "args" attribute of the route
        """
        for val in routes.values():
            for method, path in val.items():

                # treat dict as kwargs to a handler class
                if isinstance(path, dict):
                    path["handler"] = lookup(path["handler"])
                    hdlr = Handler(**path)

                # directly replace str with module
                elif isinstance(path, str):
                    hdlr = Handler(lookup(path))

                # treat as a callable
                else:
                    hdlr = Handler(path)

                val[method] = hdlr

        self._routes = routes

    def __call__(self, resource, method):
        """try to match a resource/method to a defined route"""
        for key, val in self._routes.items():
            if match := re.match(key + "$", resource):
                if path := val.get(method):
                    return Route(path.handler, match.groups(), path.silent)


def lookup(path):
    """convert a path to a module"""
    if isinstance(path, str):
        modnam, funnam = path.rsplit(".", 1)
        mod = importlib.import_module(modnam)
        path = getattr(mod, funnam)
    return path


# pylint: disable-next=too-few-public-methods
class Handler:
    def __init__(self, handler, silent=False):
        self.handler = handler
        self.silent = silent
