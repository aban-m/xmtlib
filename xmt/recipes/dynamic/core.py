try:
    from . import processor
    from ..base import Recipe, ParsingError
    from ..storage import Spec, Context, RecipeStorage
    from ..static.core import StaticRecipe
    from ..utils import without
except ImportError:
    import processor
    import sys
    sys.path.insert(0, '..')
    from base import Recipe, ParsingError
    from xmt.recipes.storage import Spec, Context, RecipeStorage, FileStorage
    from static.core import StaticRecipe
    from utils import without


# TODO:
#   1. Handle automatic detection of "expr"
#   2. Ensure that expr/return are paired correctly.
#   3. Load static recipes.
#   4. Remote inclusion caveats (e.g., cyclic dependency)
    
class DynamicRecipe(Recipe):
    def __init__(self, spec : Spec, env : RecipeStorage, stack: list = None):
        super().__init__(spec, env, stack)
        
        if self.type != 'dynamic':
            raise ParsingError(f'Exepcted a dynamic recipe, got recipe of type {self.type}')

        self.preprocess()

        self.diff = Context()
        self.env = env
        
    def preprocess(self): # TODO: Implement preprocessing
        pass
    
    def process_includes(self):
        for defn in self.spec.get('include', []):
            typ, name = tuple(defn.items())[0]
            if typ == 'dynamic':
                spec = self.env.load(name)
                recipe = DynamicRecipe(spec, self.env, self.stack)
                recipe.execute()
                self.diff[name] = recipe.diff
                
            elif typ == 'static':
                spec = self.env.load(name)
                recipe = StaticRecipe(spec, self.env, self.stack)
                recipe.execute(compile_tags = True)
                self.diff[name] = recipe # export the entire recipe
            else:
                raise ValueError('Unrecognized recipe type.')
        
    def process_var(self, var_name, var_dec):
        _var_dec = processor.interpret(without(var_dec, 'return'), self.diff)
        content = ''
        if 'path' in var_dec: 
            content = processor.load(_var_dec, self.env) # load content if possible

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
