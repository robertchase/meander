from functools import partial, wraps

from meander import exception
from meander.param import Param
from meander.document import ServerDocument as Request


def payload(include_connection_id=False, gather_extra_kwargs=False, **params):

    def adjust(param, name):
        if not isinstance(param, Param):
            param = Param(param)
        param.name = name
        return param

    params = [adjust(param, name) for name, param in params.items()]

    def inner(handler):
        @wraps(handler)
        def _inner(*args, **kwargs):

            if len(args) > len(params):
                raise exception.ExtraAttributeError(args[len(params):])

            for value, param in zip(args, params):
                if param.name in kwargs:
                    raise exception.DuplicateAttributeError(param.name)
                kwargs[param.name] = value

            connection_id = ""
            if args and isinstance(request := args[0], Request):
                args = request.args
                kwargs = request.content if request.content else {}
                connection_id = f"con={request.connection_id} req={request.id}"
            elif include_connection_id and "connection_id" in kwargs:
                connection_id = kwargs.pop("connection_id")

            kwarg_sink = {}
            if gather_extra_kwargs:
                param_names = [param.name for param in params]
                for key, val in kwargs.items():
                    if key not in param_names:
                        kwarg_sink[key] = val

            normal = []
            if include_connection_id:
                normal.append(connection_id)

            for param in params:
                if param.name not in kwargs:
                    if param.is_required:
                        raise exception.RequiredAttributeError(param.name)
                    normal.append(param.default)
                else:
                    try:
                        value = kwargs[param.name]
                        normal.append(param.type(value))
                    except ValueError as err:
                        raise exception.PayloadValueError(
                            f"'{param.name}' is {err}")

            return handler(*normal, **kwarg_sink)

        return _inner
    return inner


payload_id = partial(payload, include_connection_id=True)
