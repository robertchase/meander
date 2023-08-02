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
curl -v localhost:8080/echo -XPUT -da=10 -db=20
```

[echo-get-put](echo-put.py)