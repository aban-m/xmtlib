from collections import defaultdict

from pypdf import parse_filename_page_ranges
from .parsing import parse_index_string
from ..base import Recipe, ParsingError
from ..storage import Spec, RecipeStorage
from .processor import ContentWrapper, IndexCollection

# TODO:
#   1. VALIDATION
#   2. A script that generates the YAML files.


class StaticRecipe(Recipe):
    def __init__(self, spec: Spec, env: RecipeStorage, stack: list = None):
        super().__init__(spec, env, stack)
        self.initialize()

    def initialize(self):
        self.content = []

        if "tags" not in self.spec or not self.spec["tags"]:
            self.spec["tags"] = {}
        if "annotations" not in self.spec or not self.spec["annotations"]:
            self.spec["annotations"] = {}

        self._tags = {}
        self._special_tags = []
        self.tags = None

    def include(self, path):
        """Handles the inclusion of a static recipe."""
        subrecipe = StaticRecipe(self.env.load_recipe(path), self.env, self.stack)
        subrecipe.execute(compile_tags=False)

        precount = len(self)

        for chunk in subrecipe.content:
            self.content.append(chunk)

        for tag, what in subrecipe._tags.items():
            if tag in self.spec["tags"]:
                if isinstance(self.spec["tags"][tag], str):
                    self.spec["tags"][tag] = parse_index_string(
                        self.spec["tags"][tag], precount
                    )
            else:
                self.spec['tags'][tag] = []
            self.spec["tags"][tag].extend([
                precount + i for i in what
            ])  # HACK: Modifying the spec itself!

    def process_content(self):
        """Iterates through the 'include' section, including every recipe."""
        for item in self.spec["content"]:
            if isinstance(item, dict):
                if 'include' in item:
                    self.include(item['include'])
                elif 'tag' in item:
                    self._special_tags.append((len(self.content), item))
                else:
                    raise ParsingError('Unrecognized special content marker.')
                continue

            self.content.append(defaultdict(None, {"content": item}))

    def process_tag(self, tag, what):
        if tag not in self._tags:
            self._tags[tag] = []
        if isinstance(what, str):
            what = parse_index_string(what, len(self))
        elif isinstance(what, int): what = [what]
        self._tags[tag].extend(what)

    def process_tags(self):
        """Handles the 'tags' section."""
        for tag, what in self.spec["tags"].items():
            self.process_tag(tag, what)
        
        for i, special in self._special_tags:
            
            try:
                what = special['tag']
                tag_name = special['with']
            except KeyError:
                raise ParsingError('Malformed special tag marker.')
            
            if not tag_name in self._tags:
                self._tags[tag_name] = []

            if what == 'preceding':
                self._tags[tag_name].extend(range(1, i + 1))
            elif what == 'subsequent':
                self._tags[tag_name].extend(range(max(1, i), len(self)+1))
            else:
                raise ParsingError(f'Invalid special marker {what}')
            
        for tag_name, indices in self._tags.items():
            indices.sort()


    def process_annotations(self):
        """Handles the 'annotations' section."""
        for ann, val in self.spec["annotations"].items():
            if isinstance(val, list):
                cpos, rpos = 0, 0
                while cpos < len(val):
                    pick = val[cpos]
                    if isinstance(pick, dict):
                        if "jump" in pick:  # TODO: Handle and TEST jumping
                            rpos = pick["jump"]
                    else:
                        self.content[rpos][ann] = pick
                    cpos += 1
                    rpos += 1
            elif isinstance(val, dict):
                for ind, annval in val.items():
                    self.content[ind][ann] = annval
            else:
                raise ParsingError("Could not process annotation.")

    def compile_tags(self):
        """Optimize the tags for fast access and filtering"""
        self.tags = {}
        for tag, indices in self._tags.items():
            self.tags[tag] = IndexCollection(indices, len(self), tag)

    def execute(self, compile_tags=True):
        """Executes the recipe, making it ready for consumption."""
        # First, clear the state
        self.initialize()

        # Then, process
        self.process_content()
        self.process_tags()
        if compile_tags:
            self.compile_tags()
        self.process_annotations()

    def __getitem__(self, i):
        if isinstance(i, int) or isinstance(i, slice):
            return ContentWrapper(self.content[i])
        elif isinstance(i, str):
            return self.tags[i]
        elif isinstance(i, IndexCollection):
            return [self[j - 1] for j in i.indices]
        else:
            raise TypeError(f"Slicing is not supported for type {type(i)}")

    def __len__(self):
        return len(self.content)
