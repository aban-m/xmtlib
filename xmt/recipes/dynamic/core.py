try:
    from . import processor, parsing
    from ..base import Recipe
    from ..models import Spec, Context, Environment
    from ..utils import without
except ImportError:
    import processor, parsing
    import sys; sys.path.insert(0, '..')
    from base import Recipe
    from models import Spec, Context, Environment
    from utils import without
    
class DynamicRecipe(Recipe):
    def __init__(self, spec : Spec, env : Environment):
        super().__init__(spec, env)
        self.validate()
        
        self.diff = Context()
        self.env = env

        self.progress = 0
        
    def validate(self):
        pass
    
    def process_includes(self):
        for defn in self.spec.get('include', []):
            typ, ID = tuple(defn.items())[0]
            if typ == 'dynamic':
                spec = parsing.parse_dynamic_recipe(self.env.lookup(ID+'.yaml'))
                recipe = DynamicRecipe(spec, self.env)
                recipe.execute()
                self.diff[ID] = recipe.diff
                
            elif typ == 'static':
                raise NotImplementedError('Only dynamic recipes are supported.')
            else:
                raise ValueError('Unrecognized value.')
        self.progress = max(self.progress, 1)
        
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
        self.progress = max(self.progress, 2)

    def process_return(self):
        if 'result' in self.spec:
            self.process_var('RETURN', self.spec['result'])
        self.progress = max(self.progress, 3)

    def value(self):
        if self.progress < 3: raise Exception('Execution incomplete.')
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
        recipe = DynamicRecipe(spec, Environment('../../../samples'))
        recipe.execute()
    boot()
