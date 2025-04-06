# Route

A route defines how an HTTP `resource` is handled by a server. A list of routes is provided to a server when the `add_server` method is called. This list of routes is used to classify and handle incoming `HTTP` requests.

Each `HTTP` document sent to the server will be matched against the items in `routes`. The handler associated with the first match will be executed; if no match is found, `meander` will respond with a `404`.

## Routes file

If the `add_server` method is called with a `str` value for the `routes` argument, the value is treated as a dot-delimited path name to a file containing `route` definitions. The file is expected to be in the python path.
The file must have a file type; `.routes` is conventional.

A `routes` file is of the form (the numbers in square brackets are notes):

```
ROUTE /ping [1]
    SILENT [5]
    HANDLER pong [3]
    
ROUTE /user/(\d+)
    METHOD GET [2]
        HANDLER api.user.get [3]
    METHOD POST
        HANDLER api.user.upsert

ROUTE /foo
    METHOD PUT
        BEFORE api.before.auth [4]
        HANDLER api.foo.update
```

Each line begins with a directive (eg. ROUTE, METHOD, etc). A directive can be preceeded by whitespace, which might help with readability. A directive is *not* case sensitive.

1. A `ROUTE` directive specifies a pattern that matches the `url` of an inbound `HTTP` request.

  The pattern is prefixed with the `base_url` and postfixed with a "$", and is used as a regular expression to match against a request's `url`.
The match must be exact.
The regular expressions follow the features/rules allowed by Python.

  An inbound request will be matched against each `ROUTE` in the order that they appear in the file.
The first `ROUTE` whose pattern matches the `url` will be checked for a matching `METHOD`.

2. A `METHOD` directive specifies which `HTTP` method (for example: `GET`, `POST`, etc) must be specified in the request
in order for the request to match.
Even if a `url` matches a pattern, the `HTTP` method must also match.
If a `METHOD` is not specified for the `ROUTE`, then `GET` is assumed.
  
3. A `HANDLER` directive specifies what action to take in the event of a match.
A `HANDLER` usually points to a function using a dot-delimited path,
but it can also be a simple string.

  In the first example, the string "pong" is specified,
which means a `text/plain` response of `pong` will be returned for any matching request.
In a `HANDLER` directive, a string cannot contain a dot (.) character, or it will be interpreted as a path.

  In the second example, the `HANDLER` is interpreted as a path to a callable.
The callable `get` is loaded from the `api.user` module, which must be found in the `PYTHONPATH`.
This callable is invoked with parameter substitution based on the inspection of argument annotatons. See [...]

4. A `BEFORE` directive specifies an action to take before calling a `HANDLER` routine.
In this example, the callable `auth` is loaded from the `api.before` module (found in the `PYTHONPATH`).
This function is called with the request document as it's only argument.

  The purpose of a `BEFORE` action is to handle `HTTP` specific actions—like examining headers,
or performing authentication—before calling the `HANDLER` action. This means that the `HANDLER` action can
remain oblivious to the `HTTP` context, allowing it to be easily used outside of a web server (for instance,
from a `cli` or unit test).

5. A `SILENT` directive informs `meander` to skip logging related to the handling of a route.

  By default each connection is logged when it is opened and closed, as well as one log message for each request. Something like this:

  ```
  INFO:meander:socket=localhost:58559 cid=1
  INFO:meander:request cid=1 rid=1 method=GET resource=/ping status=200 t=0.000829
  INFO:meander:close cid=1 t=0.001207
  ```

  There is timing for the whole connection, and for each request.
The connection id (cid) and request id (rid) are logged.
The `METHOD`, `resource`, and return `HTTP status code` are recorded for each request.


## Routes dict

If the `add_server` method is called with a `dict` value for the `routes` argument, the value is treated as follows:

`routes` is a dict of the form:

```
{
    "pattern": HANDLER,
    "pattern": {
        "method": HANDLER,
        "method": {control-parameters},...
    },...
}
```

where:

* `pattern` is a regex matching an http_resorce (path); the pattern must match the complete resource
* `method` is a string matching an http_method (`GET`, `POST`, etc)
* `HANDLER` is an http handler (callable), or a dot-delimited path to an http handler (dynamically loaded), or a simple string (returned on match)
* `control-parameters` is a dict containing:

		"handler": HANDLER
	
	and any of:
	
		"silent": True|False
		"before": [callable, ...]

* `silent` is a flag that controls log messages produced by meander for each connection (default=False)
* `before` is a list of callables to execute prior to calling the
handler; each callable is invoked in order with a `meander.Request` as the only argument
	
If a pattern has only a `GET` method handler, then the dict of methods and handlers can be replaced with just a `HANDLER`.