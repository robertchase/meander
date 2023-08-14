"""simple router utility"""
from functools import namedtuple
import importlib
import re


Route = namedtuple("Route", "handler, args, silent, before")


class Router:  # pylint: disable=too-few-public-methods
    """create a router for http requests"""

    def __init__(self, routes):
        """
        "routes" is a dict of the form:
             {
                 "pattern": PATH,
                 "pattern": {
                     "method": PATH,
                     "method": {control-parameters},...
                 },...
             }

         where:
             - "pattern" is a regex matching an http_resource (path)
             - "method" is a string matching an http_method ("GET", "POST",
               etc).
             - PATH is an http handler (callable) or a dot-delimited path
               to an http handler, or a simple string
             - control-parameters is a dict containing:
                 "handler" : PATH

                 and any of:

                 "silent": True|False (see route attributes below)
                 "before": [callable, ...] (see route attributes below)

         if a pattern has only a "GET" method handler, then the dict of
         methods and paths can be replaced with just a path.

         example:
             {

                 "/ping": "pong",

                 "/user/([0-9a-f]{16})": {
                     "GET": "myapp.user.get_user",
                     "POST": "myapp.user.add_user",
                 },
             }

         the router instance is used like this:

             if route := router(http_resource, http_method):
                 # handle the http_document

         the returned route has four attributes:
             handler - callable that takes an http_document and returns
                       any result
             silent - a flag that can disable logging
             args - list of regex groups parsed from the http_resource
                    using the pattern
             before - list of callables to execute prior to calling the
                        handler; each callable is invoked in order with
                        the http_document as the only argument

         Notes:

         1. the pattern must match the complete resource.
         2. the first pattern that matches the resource wins (so, when
            there is ambiguity, put more specific patterns first).
         3. if no pattern matches the resource, None is returned
         4. if grouping parethesis are used in pattern then the grouped
            items are returned in the "args" attribute of the route
        """
        self._routes = {}
        for url, val in routes.items():
            if not isinstance(val, dict):
                val = {"GET": val}

            for method, path in val.items():
                if method in ("handler", "silent", "before"):
                    raise Exception(f"method name missing in ({method}: {path})")

                # treat dict as kwargs to a handler class
                if isinstance(path, dict):
                    path["handler"] = lookup(path["handler"])
                    hdlr = Handler(**path)

                # simple string
                elif isinstance(path, str) and "." not in path:
                    hdlr = Handler(simple_string(path))

                # directly replace dot-delimited str with callable
                elif isinstance(path, str):
                    hdlr = Handler(lookup(path))

                # treat as a callable
                else:
                    hdlr = Handler(path)

                val[method] = hdlr

            self._routes[url] = val

    def __call__(self, resource, method):
        """try to match a resource/method to a defined route"""
        for key, val in self._routes.items():
            if match := re.match(key + "$", resource):
                if path := val.get(method):
                    return Route(path.handler, match.groups(), path.silent, path.before)
        return None


def simple_string(fixed_return):
    """return a callable that returns "s" when called with a single arg"""

    def _simple_string(arg):  # pylint: disable=unused-argument
        return fixed_return

    return _simple_string


def lookup(path):
    """convert a path to a callable"""
    if isinstance(path, str) and "." not in path:
        path = simple_string(path)
    elif isinstance(path, str):
        modnam, funnam = path.rsplit(".", 1)
        mod = importlib.import_module(modnam)
        path = getattr(mod, funnam)
    return path


# pylint: disable-next=too-few-public-methods
class Handler:
    """container class for handler attributes"""

    def __init__(self, handler, silent=False, before=None):
        self.handler = handler
        self.silent = silent
        self.before = before if before else []
