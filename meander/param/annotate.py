from inspect import signature

from meander import exception, Request
from meander.param import Param, types


def get_params(fn):

    def get_type():
        if par.annotation != par.empty:
            if par.annotation in (Request, types.ConnectionId):
                return par.annotation
            if par.annotation == int:
                return types.integer
            if par.annotation == bool:
                return types.boolean
            if par.annotation == str:
                return str
            if isinstance(par.annotation, Param):
                return par.annotation
        return lambda x: x

    params = []

    sig = signature(fn)
    for par in sig.parameters.values():

        param = Param(get_type())
        param.no_annotation = par.annotation == par.empty
        param.is_request = isinstance(param.type, Request)
        param.is_connection_id = isinstance(param.type, types.ConnectionId)
        if par.default != par.empty:
            param.default = par.default
        param.name = par.name

        params.append(param)

    return params


def call(fn, request: Request):

    params = get_params(fn)

    kwargs = {}
    if len(params) == 0:
        args = []
    elif len(params) == 1 and (params[0].no_annotation or params[0].is_request):
        args = [request]
    else:
        content = request.content
        connection_id = f"con={request.connection_id} req={request.id}"

        if len(request.args) > len(params):
            raise exception.ExtraAttributeError(args[len(params):])

        for value, param in zip(request.args, params):
            if param.name in content:
                raise exception.DuplicateAttributeError(param.name)
            content[param.name] = value

        args = []
        for param in get_params(fn):
            if param.is_connection_id:
                args.append(connection_id)
            elif param.is_request:
                args.append(request)
            elif param.name not in content:
                if param.is_required:
                    raise exception.RequiredAttributeError(param.name)
                args.append(param.default)
            else:
                try:
                    value = content[param.name]
                    args.append(param.type(value))
                except ValueError as err:
                    raise exception.PayloadValueError(f"'{param.name}' is {err}")

    return fn(*args, **kwargs)
