# meander
tiny asnyc web

## introduction

The `meander` framework allows any python function to be used as an `API` endpoint. There are no variables magically injected into the frame, and no special decorators to worry about.

This is accomplished by separating the wiring of the `API` from the construction of the code. You write a function, point to the function using `meander`, and the parameters used by the function are automatically extracted from the `HTTP Request`. Functions can be defined with or without the `async` keyword; `meander` will make the correct call.

This library allows you to take the functions you've developed for your `API` and easily use them in other places from within your codebase, including `cli` code and unit tests.

## basic operation

```
import meander as web

web.add_server({"/ping": "pong"})
web.run()
```

This code creates and runs an `HTTP` server listening on port `8080` that responds to `GET` requests for `/ping` with the string "pong". This result is wrapped in a `text/plain` response.

If we saved the code in a file named `my-server.py`, then running it is a simple as this:

```
python3 my-server.py
```

--

Notes: 

* *`meander` is in the PYTHONPATH.*
* *The server will run until stopped from the terminal with `CTRL-C`.*

--

To talk to the server, use `curl` in another terminal:

```
curl -v localhost:8080/ping
* Connected to localhost (127.0.0.1) port 12345 (#0)
> GET /ping HTTP/1.1
> Host: localhost:12345
> User-Agent: curl/7.88.1
> Accept: */*
>
< HTTP/1.1 200 OK
< Content-Type: text/plain; charset=utf-8
< Date: Sat, 08 Jul 2023 09:01:37 EDT
< Content-Length: 4
<
pong
```
## logging
Log messages are automatically produced by the server using python's `logging` library.

```
import logging
import meander as web

logging.basicConfig(level=logging.INFO)

web.add_server({"/ping": "pong"})
web.run()
```
Running the server now produces log messages.

```
python3 my-server.py
INFO:meander:starting server on port 8080
```

Each `HTTP` connection and request is also logged, including a unique id (cid) for each connection and request (rid), and timing information.

```
INFO:meander:open socket=127.0.0.1:55198 cid=1
INFO:meander:request cid=1 rid=1 method=GET resource=/ping status=200 t=0.000140
INFO:meander:close cid=1 t=0.000760
```

## beyond the basics

Responding to a `url` with a simple string is not widely useful.
We'll look at some additional ways to handle client requests. 
### local function

A local or imported function is registered by using the function name:

```
def echo(request):
    return request.content
    
web.add_server({
    "/ping": "pong",
    "/echo": echo,
)}
```

A call to the `echo` endpoint produces an empty result, because no `content` was supplied.

```
curl -v localhost:8080/echo
* Connected to localhost (127.0.0.1) port 8080 (#0)
> GET /echo HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.88.1
> Accept: */*
>
< HTTP/1.1 200 OK
< Date: Sat, 22 Jul 2023 09:00:11 EDT
< Content-Length: 0
```

A `GET` method does not support content, but it does support a `query string`. Any `query string` parameters will be converted into a `dict` and stored in the `request.content` attribute. Since the `echo` handler returns the `content`, the result will contain the `dict` as `application/json` content.

```
curl -v localhost:8080/echo\?this=is\&a=test
* Connected to localhost (127.0.0.1) port 8080 (#0)
> GET /echo?this=is&a=test HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.88.1
> Accept: */*
>
< HTTP/1.1 200 OK
< Content-Type: application/json; charset=utf-8
< Date: Sat, 22 Jul 2023 09:13:15 EDT
< Content-Length: 27
<
{"this": "is", "a": "test"}
```

### supporting other methods

Let's add a `GET` and a `PUT` to the `echo` endpoint. Both methods use the same function.

```
web.add_server({
    "/ping": "pong",
    "/echo": {
        "GET": echo,
        "PUT": echo,
    },
)}
```

The `GET` call will work the same as before. What happens with `PUT`? We'll send some simple text data to the endpoint and see.

```
curl -v localhost:8080/echo -XPUT --data "this is a test" -H "content-type: text/plain"
* Connected to localhost (127.0.0.1) port 8080 (#0)
> PUT /echo HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.88.1
> Accept: */*
> content-type: text/plain
> Content-Length: 14
>
< HTTP/1.1 200 OK
< Content-Type: text/plain; charset=utf-8
< Date: Sat, 22 Jul 2023 09:40:13 EDT
< Content-Length: 14
<
this is a test
```

The data we sent was supplied in the `request.content` attribute. Although there are other attributes that show specifically what arrived in the `query string` or in the `http_content` area, `meander` attempts to coerce the input data (with specific attention to `form`, `json`, and `query string` data) into this single attribute, no matter the `HTTP` method used.

Here is a `PUT` with `form` data:

```
curl -v localhost:8080/echo -XPUT -d a=1 -d b=2
* Connected to localhost (127.0.0.1) port 8080 (#0)
> PUT /echo HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.88.1
> Accept: */*
> Content-Length: 7
> Content-Type: application/x-www-form-urlencoded
>
< HTTP/1.1 200 OK
< Content-Type: application/json; charset=utf-8
< Date: Sat, 22 Jul 2023 09:47:23 EDT
< Content-Length: 20
<
{"a": "1", "b": "2"}
```

The `form` data is converted into a `dict` and stored in `request.content`. When the content is returned by the `echo` handler, it is converted to `json`.

### automatic argument assignment

Now that we understand how `HTTP` data is converted into `dict` data in the `content` attribute of the `request`, we can have `meander` automatically supply values from that `dict` into a function.

Here is a simple add function:

```
def add(a, b):
	return a + b
	
web.add_server({"/add": add})
web.run()
```

Here, `meander` will see the parameter names and automatically look up the values by name from the `dict` in the `content` attribute. Lets try it:

```
curl localhost:8080/add\?a=10\&b=20
1020
```

We can see from the result, `1020`, that the two parameters were treated as strings and concatenated. If the purpose is to add `10` and `20`, then it makes sense to force the parameters to integer values. When the `int` annotation is added to the function signature, then `meander` will automatically do the conversion.

```
def add(a: int, b: int):
    return a + b
```

Here is the result:

```
curl localhost:8080/add\?a=10\&b=20
30
```

If `a` or `b` are not specified, or if their values cannot be coerced into integers, then a `400 Bad Request` will be returned along with a message.

```
curl localhost:8080/add\?b=2
missing required attribute: a
```

```
curl localhost:8080/add\?a=hello\&b=2
'a' is not an integer
```

### default values

Adding a default value to a function signature tells `meander` that the parameter is optional. If an optional parameter name is not found in the `content dict`, then `meander` will let `python` supply the default value in the normal way.

```
def add(a: int, b: int = 1):
    """add or increment"""
    return a + b
```

Here is the result:

```
curl localhost:8080/add\?a=10
11
```

### how meander chooses parameters

Earlier, the `echo` handler was defined with a single parameter named `request`. This parameter was supplied with an `http_document` (a `web.Request` object). How did `meander` know *not* to look for `request` in the `content` attribute's `dict`? The answer is that `meander` follows a set of rules to determine how to supply parameters to a handler function:

1. If no parameters are specified in the function, nothing is passed.
2. If one parameter is specified, and that parameter has no annotation or has an annotation of `web.Request`, then the `http_document` is passed as the only parameter.
3. If (1) and (2) don't apply, then each parameter is examined, and the *proper substitution* is applied.

##### What is the proper substitution?

* `int`, `bool` and `str` annotations will automatically perform conversions
* a `web.Request` annotation will supply the `http_document` in any parameter that specifies it
* a `web.ConnectionId` annotation will supply a string of the form `f"con={request.connection_id} req={request.id}"` which can be used to tie log messages together
* an annotation which is a subclass of `web.ParamType` will be called with the value from the `content dict`, allowing for custom types
* all other annotations are ignored and the value is passed through without change

##### How does `int` conversion work?

An `int` value must be composed of digits, and digits only. If this is the case, then the native `int` type is used to perform a base-10 conversion.

##### How does `bool` conversion work?

* 1, "1", or True returns a True
* 0, "0", or False returns a False

##### How do I create my own annotation?

The `web.ParamType` class is the super class for all user-defined annotation types. `meander` expects a `ParamType` subclass to implement the `__call__` magic method to validate and/or transform the value, returning the normalized result. Here is an example that validates social security number formats:

```
class SsnType(web.ParamType):
	def __call__(self, value):
	    if not (m := re.match(r"(\d{3})-?(\d{2})-?(\d{4})$", str(value))):
	        raise ValueError("not a properly formatted SSN")
	    return "".join(m.groups())
```

Validation errors are reported by raising a `ValueError` with a message which finishes the sentence: `'fieldname' is ...`&mdash;for instance, `'my_id' is not a properly formatted SSN`. On success, the value returned will be the value supplied to the annotated function parameter.

### non-local functions

If all of the functions that handle `meander` requests are local or imported, then the namespace of the module that makes the `add_server` call can get quite full. Another way to specify a handler function in the `add_server` call is to use the dot-delimited path to the function. If you had the `echo` function defined in a `python` file named `app/api/basic.py`, then the `add_server` call might look like this:

```
web.add_server({
    "/echo": {
        "GET": "app.api.basic.echo",
        "PUT": "app.api.basic.echo",
    }
})
```

If `meander` sees a string value for the handler that contains one or more "." characters, it dynamically loads the code when `add_server` is called.

### pre-processing

Before running the handler function, `meander` can be instructed to execute one or more functions which take a `web.Request` as a parameter. These functions can examine http headers, perform authentication, manipulate the request object, or any other steps required before running the handler function. The syntax looks like this:

```
web.add_server({
    "/ping" : {
        "GET": {
            "before": [authenticate],
            "handler": "app.basic.ping",
        },
    },
})
```

This tells `meander` to execute the `authenticate` function before calling the `ping` handler. The `authenticate` function might find a problem and have to throw a `web.HTTPException(401, "Unauthorized")`, which will prevent the handler code from being executed and return the `401` to the caller.

### the silent treatment

Sometimes pieces of the infrastructure, like a load-balancer, will call an endpoint in order to verify the health of a service. This can flood the logs with messages that aren't related to client activity. These health-check calls can be silenced&mdash;meaning no log messages will be produced by `meander`. Let's silence the `ping` handler:

```
web.add_server({"/ping": {"silent": True, "handler": "pong"})
web.run()
```

That's all there is to silencing a call. If the endpoint checks other resources, like a database or a cache service, and discovers a problem, then any messages produced by the handler will still appear in the log.