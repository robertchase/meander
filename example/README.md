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

### logging ping

This is the same as the simple ping, with logging enabled.

[logging ping](log-ping.py)


### function ping

This performs a ping from a local funtion that logs when it runs.

[function ping](function-ping.py)

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

### async handler

Defines an async handler that awaits a call to another endpoint on the same server. Since the server and the handler operate asynchronously, the async handler is able to call back to the same server without having to worry about one operation blocking the other from completing.

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

Using *before* allows for the separation of `HTTP` processing from the handler's logic. Take, for instance, performing authenticaion with `HTTP header` values. It makes more sense to perform this check prior to calling the handler so that the handler is independent from the `HTTP` context. If the authentication check was performed in a *decorator* or from within the handler itself, then the handler is no longer callable without a full `web.Request` object. 

##### example use

[before](before.py)

This provides two `GET` endpoints, `/value` and `/value/required` that are looking for an `HTTP` header named `x-value` which gets added to `request.context` with the key `value`. If the `header` is not present, `/value` will use `default-value` and `/value/required` will return a `400 Bad Request`.