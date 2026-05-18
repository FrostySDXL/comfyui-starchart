def node_info(node_class):
    # fmt: off
    info = {}
    info['input'] = node_class.INPUT_TYPES()
    info['output'] = node_class.RETURN_TYPES
    info['display_name'] = node_class.__name__
    # fmt: on
    return info
