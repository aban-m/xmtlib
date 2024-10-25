import os

try:
    from .models import Spec, RecipeStorage
except ImportError:
    from models import Spec, RecipeStorage
    
class Recipe:
    def __init__(self, spec: Spec, env: RecipeStorage):
        for attr in ['type', 'id']:
            assert attr in spec['metadata']
        for attr in ['type', 'id', 'name', 'description']:
            spec['metadata'][attr] = spec.get(attr, '')
        self.spec =  spec
        self.env = env
