from . import processor
from ..base import Recipe, ParsingError
from ..storage import Spec, Context, RecipeStorage
from ..static.core import StaticRecipe
from ..utils import without

# TODO:
#   2. Ensure that expr/return are paired correctly.
#   3. Load static recipes.
#   4. Remote inclusion caveats (e.g., cyclic dependency)
    

SOURCES = ['args', 'path', 'http']
PROCESSORS = ['jinja2', 'regex', 'jsonpath', 'xpath', 'nothing']
TYPES = ['auto', 'text', 'json', 'yaml', 'binary']

class DynamicRecipe(Recipe):
    def __init__(self, spec : Spec, env : RecipeStorage, stack: list = None):
        super().__init__(spec, env, stack)
        
        if self.type != 'dynamic':
            raise ParsingError(f'Exepcted a dynamic recipe, got recipe of type {self.type}')

        self.preprocess()

        self.diff = Context()
        self.env = env

    def preprocess(self): # TODO: Implement preprocessing
        self.spec['var'].append(
            {
                'RETURN': self.spec['result'] 
            }
        )
        for i, defn in enumerate(self.spec['var']):
            var_name, var_dec = tuple(defn.items())[0]

            if not isinstance(var_dec, dict):
                self.spec['var'][i] = {
                    var_name: {
                        'return': var_dec
                    }
                }
                var_dec = self.spec['var'][i][var_name]
            # assert only one of the sources is present
            sources_len = len([source for source in SOURCES if source in var_dec])
            if sources_len == 0:
                var_dec['args'] = []
                var_dec['_source'] = 'args'

            elif sources_len == 1:
                assert var_dec != 'jinja2', 'Cannot have a jinja2 do block in a source-based variable definition.'

                source = [source for source in SOURCES if source in var_dec][0]
                if source in ['http', 'path']:          # flesh out
                    if isinstance(var_dec[source], str):
                        var_dec[source] = {
                            'target': var_dec[source],
                            'type': 'auto'
                        }
                    assert isinstance(var_dec[source], dict)
                    if not 'type' in var_dec[source]:
                        var_dec[source]['type'] = 'auto'

                if source == 'args' and isinstance(var_dec['args'], str):
                    var_dec['args'] = [var_dec['args']]

                var_dec['_source'] = source

            else:
                raise ParsingError('Cannot have more than one source in a variable definition.')
            
            if 'do' not in var_dec:
                var_dec['do'] = 'jinja2' if sources_len == 0 and isinstance(var_dec['return'], str) else 'nothing'

            if var_dec['do'] != 'nothing' and not 'return' in var_dec:
                raise ParsingError('Cannot have a do block without a return statement.')

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
        # Resolution step
        _var_dec = var_dec.copy()
        source = var_dec['_source']
        _var_dec[source] = processor.interpret(var_dec[source], self.diff)

        # Fetching step
        fetched, type, strict = None, None, False
        if source == 'args':
            fetched = [self.diff[arg] for arg in var_dec['args']]

        elif source == 'path':
            fetched, type = processor.load_local(_var_dec['path'], self.env)
            if _var_dec['path']['type'] == 'auto' and type:
                _var_dec['path']['type'] = type

        elif source == 'http':
            strict = True   # adherence is strict
            # TODO: Make this more general
            fetched, type = processor.load_remote(_var_dec['http'])
            if _var_dec['http']['type'] == 'auto' and type:
                _var_dec['http']['type'] = type

        else:
            raise ValueError('Unrecognized source type.') # should not be reached.

        # casting
        fetched = processor.cast(type, fetched)

        # Finalization
        if 'return' in _var_dec:
            value = processor.process(_var_dec['do'], fetched, _var_dec['return'], self.diff)
        else:
            value = fetched

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