def comfytype(*, io_type):
    def decorator(cls):
        return cls

    return decorator


class ComfyTypeIO:
    pass


class WidgetInput:
    pass


class Model3DDict:
    pass


@comfytype(io_type="BOOLEAN")
class Boolean(ComfyTypeIO):
    Type = bool

    class Input(WidgetInput):
        def __init__(self, id: str, default: bool = None):
            pass


@comfytype(io_type="STRING")
class String(ComfyTypeIO):
    Type = str

    class Input(WidgetInput):
        def __init__(self, id: str, multiline: bool = False, default: str = None):
            pass


@comfytype(io_type="LOAD_3D")
class Load3D(ComfyTypeIO):
    Type = Model3DDict


@comfytype(io_type="LOAD_3D_ANIMATION")
class Load3DAnimation(Load3D): ...
