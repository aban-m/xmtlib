from ast import expr
from . import processor
from ..base import Recipe, ParsingError
from ..storage import Spec, Context, RecipeStorage
from ..static.core import StaticRecipe
from ..utils import without

# TODO:
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
                spec = self.env.load_recipe(name)
                recipe = DynamicRecipe(spec, self.env, self.stack)
                recipe.execute()
                self.diff[name] = recipe.diff # TODO: The identifier should be the ID
                
            elif typ == 'static':
                spec = self.env.load_recipe(name)
                recipe = StaticRecipe(spec, self.env, self.stack)
                recipe.execute(compile_tags = True)
                self.diff[name] = recipe # TODO: The identifier should be the ID
            else:
                raise ValueError('Unrecognized recipe type.')
        
    def process_var(self, var_name, var_dec):
        _var_dec = processor.interpret(without(var_dec, 'return'), self.diff)
        content = ''
        if 'path' in var_dec: 
            content, typ = processor.load(_var_dec, self.env) # load content if possible
            _var_dec['type'] = typ

        value = content # by default, the return value is the loaded content.

        if 'return' in var_dec: # resolve return expression, altering the return value
            try:
                expr = _var_dec['expr']
            except KeyError:        # expression type not specified, must be inferred from context
                expr = processor.TYP_EXPR_MAP[_var_dec['type']] if 'path' in _var_dec\
                        else 'jinja2'                                                   # default to jinja2
            value = processor.resolve_expression(
                expr, var_dec['return'],        
                {**self.diff, var_name: value}, var_name
            )
        
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