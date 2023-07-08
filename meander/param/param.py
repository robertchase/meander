from meander.param import types


class Param:
    NO_DEFAULT = type("EMPTY", (), dict())

    def __init__(self, ptype=str, default=NO_DEFAULT):
        if ptype == str:
            ptype = types.String()
        elif ptype == int:
            ptype = types.integer
        elif ptype == bool:
            ptype = types.boolean
        elif isinstance(ptype, type):  # meh
            ptype = ptype()
        self.type = ptype
        self.is_required = True if default == self.NO_DEFAULT else False
        self.default = default
        self.name = None
