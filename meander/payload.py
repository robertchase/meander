from meander.param import Param
from meander.request import Request


class ExtraAttributeError(AttributeError):
    def __init__(self, name):
        self.args = (f"extra attribute(s): {', '.join(name)}",)


class DuplicateAttributeError(AttributeError):
    def __init__(self, name):
        self.args = (f"duplicate attribute: {name}",)


class RequiredAttributeError(AttributeError):
    def __init__(self, name):
        self.args = (f"missing required attribute: {name}",)


def payload(include_connection_id=False, **params):

    def adjust(param, name):
        if not isinstance(param, Param):
            param = Param(param)
        param.name = name
        return param

    params = [adjust(param, name) for name, param in params.items()]

    def inner(handler):
        def _inner(*args, **kwargs):

            if args and isinstance(request := args[0], Request):
                args = request.args
                kwargs = request.content if request.content else {}

            if len(args) > len(params):
                raise ExtraAttributeError(args[len(params):])

            for value, param in zip(args, params):
                if param.name in kwargs:
                    raise DuplicateAttributeError(param.name)
                kwargs[param.name] = value

            normal = []
            for param in params:
                if param.name not in kwargs and param.is_required:
                    raise RequiredAttributeError(param.name)
                if param.name not in kwargs:
                    normal.append(param.default)
                else:
                    try:
                        normal.append(param.type(kwargs[param.name]))
                    except ValueError as err:
                        raise ValueError(f"'{param.name}' is {err}")

            return handler(*normal)

        return _inner
    return inner
