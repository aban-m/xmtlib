try:
    from . import processor, parsing
    from ..base import Recipe
    from ..models import Spec, Context, RecipeStorage
    from ..utils import without
except ImportError:
    import processor, parsing
    import sys; sys.path.insert(0, '..')
    from base import Recipe
    from models import Spec, Context, RecipeStorage, FileStorage
    from utils import without


# TODO:
#   1. Handle automatic detection of "expr"
#   2. Ensure that expr/return are paired correctly.
#   3. Load static recipes.
#   4. Remote inclusion caveats (e.g., cyclic dependency)
    
class DynamicRecipe(Recipe):
    def __init__(self, spec : Spec, env : RecipeStorage):
        super().__init__(spec, env)
        self.validate()
        
        self.diff = Context()
        self.env = env
        
    def validate(self):
        # TODO: Implement validation
        pass # really?
    
    def process_includes(self):
        for defn in self.spec.get('include', []):
            typ, name = tuple(defn.items())[0]
            if typ == 'dynamic':
                spec = DynamicRecipe(self.env.load(name), self.env)
                recipe.execute()
                self.diff[name] = recipe.diff
                
            elif typ == 'static':
                raise NotImplementedError('Only dynamic recipes are supported.') # TODO: Implement
            
            else:
                raise ValueError('Unrecognized recipe type.')
        
    def process_var(self, var_name, var_dec):
        _var_dec = processor.interpret(without(var_dec, 'return'), self.diff)
        content = ''
        if 'path' in var_dec: content = processor.load(_var_dec, self.env) # load content if possible

        value = content
        if 'return' in var_dec: 
            value = processor.resolve_expression(var_dec['expr'], var_dec['return'], {**self.diff, var_name: content}, var_name)
        self.diff[var_name] = value
        
    def process_vars(self):
        for defn in self.spec['var']:
            var_name, var_dec  = tuple(defn.items())[0]
            self.process_var(var_name, var_dec)

    def process_return(self):
        if 'result' in self.spec:
            self.process_var('RETURN', self.spec['result'])

    def value(self):
        return self.diff['RETURN']

    def execute(self):
        self.process_includes()
        self.process_vars()
        self.process_return()
        return self.diff, self.diff.get('RETURN', None)
        
        

if __name__ == '__main__':
    import yaml
    NAME = 'sample-main.yaml'
    def boot():
        global recipe, spec
        spec = yaml.safe_load(open(f'../../../samples/{NAME}'))
        recipe = DynamicRecipe(spec, FileStorage('../../../samples'))
        recipe.execute()
    boot()
