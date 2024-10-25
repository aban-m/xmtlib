import os, sys

import json
import re
from jinja2 import Template
from collections import defaultdict

try:
    from .parsing import parse_index_string
    from ..base import Recipe
    from ..models import Spec, RecipeStorage
    from .processor import IndexCollection
    from ..models import CyclicDependencyException
    
except ImportError:
    sys.path.append('..')
    from base import Recipe
    from models import Spec, RecipeStorage, FileStorage
    from parsing import parse_index_string
    from processor import IndexCollection
    from models import CyclicDependencyException


# TODO:
#   1. VALIDATION
#   2. A script that generates the YAML files.


class StaticRecipe(Recipe):
    def __init__(self, spec: Spec, env: RecipeStorage, stack = None):
        super().__init__(spec, env)

        self.stack = stack if stack is not None else []
        if self.id in self.stack: # Catch circular dependencies
            raise CyclicDependencyException(f'Circular dependency detected: {self.id} ultimately calls itself.')
        self.stack.append(self.id)

        self.content = []

        if not 'tags' in self.spec or not self.spec['tags']: self.spec['tags'] = {}
        if not 'annotations' in self.spec or not self.spec['annotations']: self.spec['annotations'] = {}

        self._tags = {}
        self.tags = None

    def include(self, path):
        ''' Handles the inclusion of a static recipe. '''
        subrecipe = StaticRecipe(self.env.load(path), self.env, self.stack)
        subrecipe.execute(compile_tags = False)

        precount = len(self)

        for chunk in subrecipe.content:
            self.content.append(chunk)

        for tag, what in subrecipe._tags.items():
            if tag in self.spec['tags']:
                if isinstance(self.spec['tags'][tag], str):
                    self.spec['tags'][tag] = parse_index_string(self.spec['tags'][tag], precount)
            self.spec['tags'][tag].extend([precount + i for i in what]) # HACK: Modifying the spec itself!
        
    def process_content(self):
        ''' Iterates through the 'include' section, including every recipe. '''
        for item in self.spec['content']:
            if isinstance(item, dict):
                if 'include' in item: self.include(item['include'])
                continue
            self.content.append(defaultdict(None, {'content': item}))

    def process_tag(self, tag, what):
        if not tag in self._tags:
            self._tags[tag] = []
        if isinstance(what, str): what = parse_index_string(what, len(self))
        self._tags[tag].extend(what)
    def process_tags(self):
        ''' Handles the 'tags' section. '''
        for tag, what in self.spec['tags'].items():
            self.process_tag(tag, what)
            
    def process_annotations(self):
        ''' Handles the 'annotations' section. '''
        for ann, val in self.spec['annotations'].items():
            if isinstance(val, list):
                cpos, rpos = 0, 0
                while cpos < len(val):
                    pick = val[cpos]
                    if isinstance(pick, dict):
                        if 'jump' in pick: # TODO: Handle and TEST jumping 
                            rpos = pick['jump'] + 1
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
        # First, clear the state
        self.content = []
        self._tags = {}
        self.tags = None

        # Then, process
        self.process_content()
        self.process_tags()
        if compile_tags: self.compile_tags()
        self.process_annotations()

    def __getitem__(self, i): 
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
        recipe = StaticRecipe(spec, FileStorage.current())
        recipe.execute()
    boot()
