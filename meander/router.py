"""simple router utility"""

from functools import namedtuple
import importlib
import os
import re


Endpoint = namedtuple("Endpoint", "handler, args, silent, before")


class Route:  # pylint: disable=too-few-public-methods
    """Container for a single route."""

    # pylint: disable-next=too-many-arguments
    def __init__(
        self, handler, resource, method="GET", before=None, silent=False, base_url=None
    ):
        self.handler = lookup_by_path(handler)
        if base_url:
            resource = base_url.rstrip("/") + "/" + resource.lstrip("/")
        self.resource = re.compile(resource + "$")
        self.method = method
        self.silent = silent

        self.before = []
        if before is not None:
            for path in before:
                self.before.append(lookup_by_path(path))

    def match(self, resource, method):
        """Return Endpoint if specified resource and method match."""
        if match := self.resource.match(resource):
            if self.method == method:
                return Endpoint(self.handler, match.groups(), self.silent, self.before)
        return None


def lookup_by_path(path):
    """Get handler by dot-delimited path."""

    def simple_string(value: str):
        """Simple closure that returns value when called."""

        def _simple_string():
            return value

        return _simple_string

    if isinstance(path, str):
        if "." in path:
            modnam, funnam = path.rsplit(".", 1)
            mod = importlib.import_module(modnam)
            path = getattr(mod, funnam)
        else:
            path = simple_string(path)

    return path


class Router:  # pylint: disable=too-few-public-methods
    """create a router for http requests"""

    def __init__(self, routes: list[Route]):
        self.routes = routes

    def __call__(self, resource: str, method: str) -> Endpoint | None:
        """Try to match a resource+method to a defined route.

        If a matching route is found, an Endpoint is returned, else None.
        """
        for route in self.routes:
            if endpoint := route.match(resource, method):
                return endpoint
        return None


def from_dict(config: dict, base_url=None) -> Router:
    """Build a Router from a dict."""
    routes = []
    for url, val in config.items():
        kwargs = {}
        if base_url:
            url = base_url.rstrip("/") + "/" + url.lstrip("/")
        kwargs["resource"] = url

        if not isinstance(val, dict):
            val = {"GET": val}

        for method, path in val.items():
            if method in ("handler", "silent", "before"):
                raise AttributeError(f"method name missing in ({method}: {path})")

            kwargs["method"] = method

            if isinstance(path, dict):
                kwargs.update(path)

            else:
                kwargs["handler"] = path

        routes.append(Route(**kwargs))
    return Router(routes)


class RouteNotDefinedError(Exception):
    """Indicate that ROUTE is not first directive in file."""

    def __init__(self, line, directive):
        self.args = (f"line {line}: {directive} encountered before ROUTE",)


class HandlerNotDefinedError(Exception):
    """Indicate that HANDLER directive not specified."""

    def __init__(self, resource):
        self.args = (f"HANDLER not defined for {resource}",)


class NoParametersExpectedError(Exception):
    """Indicate wrong number of directive parameters."""

    def __init__(self, line, directive):
        self.args = (f"line {line}: {directive} must have no parameters",)


class OneParameterExpectedError(Exception):
    """Indicate wrong number of directive parameters."""

    def __init__(self, line, directive):
        self.args = (f"line {line}: {directive} must have one parameter",)


class DuplicateDirectiveError(Exception):
    """Indicate duplicate config directive."""

    def __init__(self, line, directive):
        self.args = (f"line {line}: {directive} specified more than once",)


class UnexpectedDirectiveError(Exception):
    """Indicate unknown config directive."""

    def __init__(self, line, directive):
        self.args = (f"line {line}: Invalid directive '{directive}'",)


def dot_delimited_to_path(path: str, extension: str = "routes") -> str:
    """Turn dot-delimited path into a directory path."""
    parts = path.split(".")
    if parts[-1] != extension:
        raise ValueError(f"Expecting '{extension}' file, not '{path}'.")
    spec = importlib.util.find_spec(parts[0])
    base_dir = spec.submodule_search_locations[0]
    return os.path.join(base_dir, *parts[1:-1]) + f".{extension}"


def parse_line(line: str) -> tuple[str, list[str]] | tuple[None, None]:
    """Parse a line into a directive and any arguments."""
    if match := re.match(r"(.*?)(?<!\\)#", line):  # look for comment
        line = match.group(1)
    if len(line := line.strip()) == 0:
        return None, None
    parts = line.split()
    return parts[0].upper(), parts[1:]


def from_config(config_path: str, base_url: str = "") -> Router:
    """Build router from config file."""

    def add_route():
        """Add a new route."""
        if route:
            if "handler" not in route:
                raise HandlerNotDefinedError(route["resource"])
            routes.append(Route(**route))

    def one_parameter():
        """Return the one and only parameter."""
        if len(args) != 1:
            raise OneParameterExpectedError(line_no, directive)
        return args[0]

    def no_parameters():
        """Check that no parameters were supplied."""
        if len(args) != 0:
            raise NoParametersExpectedError(line_no, directive)

    def no_duplicates(key):
        """Make sure that directive is not a duplicate for this route."""
        if key in route:
            raise DuplicateDirectiveError(line_no, directive)

    def add_method(method):
        """Add method to route if not already present."""
        if method in methods:
            raise DuplicateDirectiveError(line_no, method)
        methods.add(method)
        route["method"] = method

    routes = []
    route = {}
    with open(dot_delimited_to_path(config_path), encoding="utf-8") as config:
        for line_no, line in enumerate(config.readlines(), start=1):

            directive, args = parse_line(line)

            if directive is None:
                pass

            elif directive == "ROUTE":
                add_route()
                route = {"resource": one_parameter(), "base_url": base_url}
                methods = set()

            elif not route:
                raise RouteNotDefinedError(line_no, directive)

            elif directive == "METHOD":
                if "method" in route:
                    add_route()
                    route = {
                        key: val
                        for key, val in route.items()
                        if key in ("resource", "base_url")
                    }
                add_method(one_parameter().upper())

            elif directive == "HANDLER":
                no_duplicates("handler")
                if "method" not in route:
                    add_method("GET")
                route["handler"] = one_parameter()

            elif directive == "BEFORE":
                route.setdefault("before", []).append(one_parameter())

            elif directive == "SILENT":
                no_parameters()
                no_duplicates("silent")
                route["silent"] = True

            else:
                raise UnexpectedDirectiveError(line_no, directive)

        add_route()

        return Router(routes)
