# TODO: Refactor.
from .dynamic.core import DynamicRecipe
from .static.core import StaticRecipe

TYPES_MAP = {
    'dynamic': DynamicRecipe,
    'static': StaticRecipe
}

def without(d : dict, *keys):
    return {k : d[k] for k in d if not k in keys}

def attach(d1, d2): return {**d1, **d2}

def bootstrap(spec: dict, *args, **kwargs):
    return TYPES_MAP[spec['metadata']['type']](spec, *args, **kwargs)