# meander examples

### simple ping

This is about the simplest web server that you can make with `meander`. A server with one `GET` endpoint named `/ping` that returns a "text/plain" response of "pong".

[ping/pong](ping.py)


##### running the examples


As for all the examples, the `PYTHONPATH` must include `meander` in order to run the program. Start the server with:

```
python3 -m example.ping
```

In another terminal use `curl` to make the call:

```
curl -v localhost:8080/ping
```

Stop the server with `CNTL-c`.

### enabling logging

This is the same as the simple ping, with logging enabled.

[logging ping](log-ping.py)

Running this server produces log messages similar to this:

```
python3 -m example.log-ping
INFO:meander:starting server on port 8080
```

Each `HTTP` connection and request is also logged, including a unique id (cid) for each connection and request (rid), and timing information.

```
INFO:meander:open socket=127.0.0.1:55198 cid=1
INFO:meander:request cid=1 rid=1 method=GET resource=/ping status=200 t=0.000140
INFO:meander:close cid=1 t=0.000760
```

### using a local function as a handler

This performs a ping from a locally defined function.

[function ping](function-ping.py)

### using a non-local function as a handler

If all of the functions that handle `meander` requests are local or imported, then the namespace of the module that makes the `add_server` call can get quite full. Another way to specify a handler function is to use the dot-delimited path to the function.

When `meander` sees a string value for the handler that contains one or more "." characters, it dynamically loads the code when add_server is called.

Here is an server that *references* the `ping` function from the `function-ping` module:

[reference ping](reference-ping.py)

### silent handling

Sometimes pieces of the infrastructure, like a load-balancer, will call an endpoint in order to verify the health of a service. This can flood the logs with messages that aren't related to client activity. These health-check calls can be silenced&mdash;meaning no log messages will be produced by `meander`.

This server defines a `GET ping` call that `meander` will silently run. Notice that the log message produced by the handler still appears in the log.

[silent ping](skip-log-ping.py)

### echo server

Add an `/echo` endpoint that responds to a `GET` with a "application/json" dictionary of the query parameters.

Use `curl` like this:

```
curl -v localhost:8080/echo?a=1&b=2
```

*Note: you may have to escape the `?` and `&` characters in your terminal, or put the entire url in quotes.*

[echo](echo.py)

### echo server that supports GET and PUT

`GET` still works for `/echo`, but so does `PUT`.

Use `curl` to execute a `PUT` like this:

```
curl -v localhost:8080/echo -XPUT -d a=10 -d b=20
```

[echo-get-put](echo-put.py)

### automatic argument assignment

The variables defined in a `GET` call's query string, or in the `form` or `json` content of another method's body are available for assignment to a function's arguments.

Here is a simple add function that adds two required parameters together:

[simple add](add.py)

```
curl localhost:8080/add\?a=10\&b=20
1020
```

We can see from the result, `1020`, that the two parameters were treated as strings and concatenated. If the purpose is to add `10` and `20`, then it makes sense to force the parameters to integer values. When the `int` annotation is added to the function signature, then `meander` will automatically do the conversion.

[add numbers](add-numbers.py)

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

By giving the second parameter a default value of `1`, we make it optional and change the function to an add/increment.

[add or increment](add-or-increment.py)

```
curl localhost:8080/add\?a=41
42
```

### async handler

An async handler allows other things to happen during I/O operations. This example makes a call to another endpoint on the same server. Since the server and the handler operate asynchronously, the async handler is able to call back to the same server without having to worry about one operation blocking the other from completing.

[async-ping](async-ping.py)

Call the async handler with `curl localhost:8080/pingping`.

These log messages show how the `/ping` call (`cid=2`) starts after the `pingping` call (`cid=1`) and finishes before `pingping` returns a result.

```
INFO:meander:socket=127.0.0.1:51886 cid=1
INFO:meander:socket=::1:51887 cid=2
INFO:meander:request cid=2 rid=2 method=GET resource=/ping status=200 t=0.000830
INFO:meander:request cid=1 rid=1 method=GET resource=/pingping status=200 t=0.007414
INFO:meander:close cid=2 t=0.001590
INFO:meander:close cid=1 t=0.007753
```

### before processing

One or more functions can be executed *before* the handler gets called. These can be thought of like *decorators*, but instead of being added directly to the handler, they are described as part of the `web` router.

##### why is this useful?

Using *before* allows for the separation of `HTTP` processing from the handler's logic. Take, for instance, performing authenticaion with `HTTP header` values. It makes more sense to perform this check prior to calling the handler so that the handler is independent from the `HTTP` context. If the authentication check was performed in a *decorator* or from within the handler itself, then the handler is no longer callable without a full `HTTP Request` object.

##### example use

[before](before.py)

This provides two `GET` endpoints, `/value` and `/value/required` that are looking for an `HTTP` header named `x-value` which gets added to `request.context` with the key `value`. If the `header` is not present, `/value` will use `default-value` and `/value/required` will return a `400 Bad Request`.
