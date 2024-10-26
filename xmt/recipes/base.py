from .storage import Spec, RecipeStorage, CyclicDependencyException

class ParsingError(Exception): pass

class Recipe:
    def __init__(self, spec: Spec, env: RecipeStorage, stack: list = None):        
        for attr in ['type', 'id']:
            assert attr in spec['metadata']
            setattr(self, attr, spec['metadata'][attr])
        for attr in ['type', 'id', 'name', 'description']:
            spec['metadata'][attr] = spec.get(attr, '')
        self.spec =  spec
        self.env = env

        self.stack = stack if stack is not None else []
        if self.id in self.stack:  # Catch circular dependencies
            raise CyclicDependencyException(
                f"Circular dependency detected: {self.id} ultimately calls itself."
            )
        self.stack.append(self.id)
