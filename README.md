# meander
tiny asnyc web

[![Testing: pytest](https://img.shields.io/badge/testing-pytest-yellow)](https://docs.pytest.org)
[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/mit/)


## introduction

The `meander` package allows any python function to be used as an `API` endpoint. There are no variables magically injected into the frame, and no special decorators to worry about.

This is accomplished by separating the wiring of the `API` from the construction of the code. You write a function, point to the function using `meander`, and the parameters used by the function are automatically extracted from the `HTTP Request`. Functions can be defined with or without the `async` keyword; `meander` will make the correct call.

This package allows you to take the functions you've developed for your `API` and easily use them in other places from within your codebase, including `cli` code and unit tests.

## a simple function

### echo

This function, `echo`, takes three parameters, the third parameter being optional with a `None` default. The annotations are standard `python` syntax, but only provide hints at the values that the function expects. When wired to `meander`, these values are pulled from the `HTTP Request` by name, and passed to the function *after proper type validation and coersion based on the annotations*.

```
def echo(a: int, b: bool, c: str = None):
    return {"a": a, "b": b, "c": c}
```

### wire it up

Here is a complete server that listens on port `8080` and responds to `GET /echo` requests by calling the `echo` function.

```
import meander as web

def echo(a: int, b: bool, c: str = None):
    return {"a": a, "b": b, "c": c}
    
web.add_server({"/echo": echo})
web.run()
```

### test out the server

Start the server and open a new terminal to run `curl`.

```
curl localhost:8080/echo
missing required attribute: a
```

We see that the required parameter `a` is missing. This is returned in a `400 Bad Request` response.

Provide a value for `a`.

```
curl localhost:8080/echo\?a=1
missing required attribute: b
```

Now `b` is missing.

Provide a value for `b`.

```
curl localhost:8080/echo\?a=1\&b=0
{"a": 1, "b": false, "c": null}
```

The `echo` function is called and returns a dict of the parameters containing the proper variable types based on the function's annotations. This is returned as an `application/json` response, which is inferred from the dict data structure that is returned from the `echo` function.

What happens if we provide values that don't match the function's annotations?

```
curl localhost:8080/echo\?a=hi
'a' is not an integer

curl localhost:8080/echo\?a=1\&b=hi
'b' is not a boolean
```

Reasonable messages are returned as `400 Bad Request` responses.

## learning more

There are more things you can do with `meander` including logging, listening on multiple ports, using `ssl`, pre-processing the `HTTP Request`, and creating your own types for annotation, to name a few.

Start with the `examples` directory to see `meander` in action.