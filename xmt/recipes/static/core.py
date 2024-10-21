import os, sys

import json
import re
from jinja2 import Template
from collections import defaultdict


try:
    from .utils import *
    from .parse import parse_static_recipe, parse_index_string
    from ..base import Recipe
    from ..models import Context, Spec, Environment
    
except ImportError:
    sys.path.append('..')
    from base import Recipe
    from models import Context, Spec, Environment
    from utils import *
    from parsing import parse_static_recipe, parse_index_string

class StaticRecipe(Recipe):
    def __init__(self, spec: Spec, env: Environment):
        super().__init__(spec, env)

        self.content = []
        self._content_len = None

        if not 'tags' in self.spec or not self.spec['tags']: self.spec['tags'] = {}
        if not 'annotations' in self.spec or not self.spec['annotations']: self.spec['annotations'] = {}

        self.tags = defaultdict(list)
        
    def include(self, path):
        subrecipe = StaticRecipe(parse_static_recipe(self.env.lookup(path)), self.env)
        subrecipe.execute()

        precount = len(self.content)
        for chunk in subrecipe.content:
            self.content.append(chunk)

        for tag, what in subrecipe.tags.items():
            self.tags[tag].extend([precount+i for i in what])
        
    def process_includes(self):
        for item in self.spec['content']:
            if isinstance(item, dict):
                if 'include' in item: self.include(item['include'])
                continue
            self.content.append(defaultdict(str, {'content': item}))
        self._content_len = len(self.content)

    def process_tags(self):
        for tag, indstr in self.spec['tags'].items():
            self.tags[tag] = parse_index_string(indstr, self._content_len)
            
    def process_annotations(self):
        for ann, val in self.spec['annotations'].items():
            if isinstance(val, list):
                cpos, rpos = 0, 0
                while cpos < len(val):
                    pick = val[cpos]
                    if isinstance(pick, dict):
                        if 'jump' in pick:
                            rpos = pick['jump']
                    else:
                        self.content[rpos][ann] = pick
                    cpos += 1; rpos += 1
            elif isinstance(val, dict):
                for ind, annval in val.items():
                    self.content[ind][ann] = annval
            else:
                raise TypeError('Could not process annotation.')

    def execute(self):
        self.process_includes()
        self.process_tags()
        self.process_annotations()

if __name__ == '__main__':
    import yaml
    import os
    os.chdir('../../../samples')
    def boot():
        global spec, recipe
        spec = yaml.safe_load(open('archetype.yaml'))
        recipe = StaticRecipe(spec, Environment.current())
        recipe.execute()
    boot()
