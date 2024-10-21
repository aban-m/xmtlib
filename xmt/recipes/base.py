import os

try:
    from .models import Spec, Environment
except ImportError:
    from models import Spec, Environment
    
class Recipe:
    def __init__(self, spec: Spec, env: Environment):
        for attr in ['type', 'id']:
            assert attr in spec['metadata']
        for attr in ['type', 'id', 'name', 'description']:
            spec['metadata'][attr] = spec.get(attr, '')
        self.spec =  spec
        self.env = env
