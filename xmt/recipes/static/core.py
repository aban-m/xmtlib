import os, sys

import json
import re
from jinja2 import Template
from collections import defaultdict


try:
    from .utils import *
    from .parsing import parse_static_recipe, parse_index_string
    from ..base import Recipe
    from ..models import Spec, Environment
    from .processor import IndexCollection
    
except ImportError:
    sys.path.append('..')
    from base import Recipe
    from models import Spec, Environment
    from utils import *
    from parsing import parse_static_recipe, parse_index_string
    from processor import IndexCollection


# TODO:
#   1. VALIDATION
#   2. A script that generates the YAML files.
#   3. Graceful handling of inclusion
#   4. Cleaning up the code in general (this is a resurrection)


class StaticRecipe(Recipe):
    def __init__(self, spec: Spec, env: Environment):
        super().__init__(spec, env)

        self.content = []

        if not 'tags' in self.spec or not self.spec['tags']: self.spec['tags'] = {}
        if not 'annotations' in self.spec or not self.spec['annotations']: self.spec['annotations'] = {}

        self._tags = {}
        self.tags = None

    def include(self, path):
        ''' Handles the inclusion of a static recipe. '''
        subrecipe = StaticRecipe(parse_static_recipe(self.env.lookup(path)), self.env)
        subrecipe.execute(compile_tags = False)

        precount = len(self.content)
        for chunk in subrecipe.content:
            self.content.append(chunk)

        for tag, what in subrecipe._tags.items():
            if not tag in self._tags:
                self._tags[tag] = [] # initializing a new tag container
            self._tags[tag].extend([precount+i for i in what])
        
    def process_includes(self):
        ''' Iterates through the 'include' section, including every recipe. '''
        for item in self.spec['content']:
            if isinstance(item, dict):
                if 'include' in item: self.include(item['include'])
                continue
            self.content.append(defaultdict(None, {'content': item}))

    def process_tags(self):
        ''' Handles the 'tags' section. '''
        for tag, indstr in self.spec['tags'].items():
            self._tags[tag] = parse_index_string(indstr, len(self))
            
    def process_annotations(self):
        ''' Handles the 'annotations' section. '''
        for ann, val in self.spec['annotations'].items():
            if isinstance(val, list):
                cpos, rpos = 0, 0
                while cpos < len(val):
                    pick = val[cpos]
                    if isinstance(pick, dict):
                        if 'jump' in pick: # TODO: Handle jumping 
                            rpos = pick['jump']
                    else:
                        self.content[rpos][ann] = pick
                    cpos += 1; rpos += 1
            elif isinstance(val, dict):
                for ind, annval in val.items():
                    self.content[ind][ann] = annval
            else:
                raise TypeError('Could not process annotation.')

    def compile_tags(self):
        ''' Optimize the tags for fast access and filtering '''
        self.tags = {}
        for tag, indices in self._tags.items():
            self.tags[tag] = IndexCollection(indices, len(self), tag)

    def execute(self, compile_tags = True):
        ''' Executes the recipe, making it ready for consumption. '''
        self.process_includes()
        self.process_tags()
        if compile_tags: self.compile_tags()
        self.process_annotations()

    def __getitem__(self, i): # TODO: Test
        if isinstance(i, int) or isinstance(i, slice): return self.content[i]
        elif isinstance(i, str): return self.tags[i]
        elif isinstance(i, IndexCollection):
            return [self[j-1] for j in i.indices]
        else: raise TypeError(f'Slicing is not supported for type {type(i)}')
    
    def __len__(self): return len(self.content)
    

if __name__ == '__main__':
    import yaml
    import os
    os.chdir('../../../samples')
    def boot():
        global spec, recipe
        spec = yaml.safe_load(open('recipe-archetype.yaml'))
        recipe = StaticRecipe(spec, Environment.current())
        recipe.execute()
    boot()
