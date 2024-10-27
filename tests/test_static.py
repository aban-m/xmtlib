import pytest

import sys
from copy import deepcopy


from ..xmt.recipes.static import parsing
from ..xmt.recipes.static.core import StaticRecipe
from ..xmt.recipes.storage import CyclicDependencyException, MemoryStorage

@pytest.fixture
def basic_recipe():
    spec = {
            'metadata': {
                'name': 'test',
                'type': 'static',
                'content': 'hello world',
                'id': 'test-basic'
            },
            'content': ['line1', 'line2', 'line3'],
            'tags': {
                'all': '1..3',
                'first': '1',
                'last_two': '2,3'
            },
            'annotations': {
                'comment': ['first comment', 'second comment', 'third comment']
            }
    }
    env = MemoryStorage()
    env['basic'] = spec
    recipe = StaticRecipe(spec, env)
    return recipe


@pytest.fixture
def cyclic_dependency_recipe(request):
# get the value of basic_recipe
    basic = request.getfixturevalue('basic_recipe')
    basic.spec['content'].append({'include': 'basic'})
    return basic

class TestTags:
    def test_simple(self, basic_recipe):
        basic_recipe.execute()
        # simple tests
        assert basic_recipe._tags['all'] == [1, 2, 3]
        assert basic_recipe._tags['first'] == [1]
        assert basic_recipe._tags['last_two'] == [2, 3]
        # complex tests
        assert (~basic_recipe['all']).indices == []
        assert (basic_recipe['first'] | basic_recipe['last_two']).indices == [1, 2, 3]


class TestInclude:
    # mark as expected failure
    def test_cyclic_dependency(self, cyclic_dependency_recipe):
        rec_lim = sys.getrecursionlimit()
        sys.setrecursionlimit(100)
        try:
            cyclic_dependency_recipe.execute()
        except CyclicDependencyException:
            pass  # expected
        except RecursionError:
            pytest.fail('Cyclic dependency not caught.')
        finally:
            sys.setrecursionlimit(rec_lim)  # reset the recursion limit.

    def test_attachments_integration(self, basic_recipe):
        # set up the environment
        clone_spec = deepcopy(basic_recipe.spec)
        clone_spec['metadata']['id'] = 'dep'
        clone_spec['metadata']['name'] = 'dep'
        clone_spec['annotations'] = {
            'extra-comment': [
                'first comment from outside', 
                'second comment from outside', 
                'third']
        }

        # add the dependency
        basic_recipe.spec['content'].append({'include': 'dep'})
        basic_recipe.env['dep'] = clone_spec        # enough to initiate a clone
        basic_recipe.execute()

        # check the tags
        assert basic_recipe._tags['all'] == list(range(1, 7))
        assert basic_recipe._tags['first'] == [1, 4]
    
        # check the annotations: the attached ones should have extra comments.
        assert all('extra-comment' in basic_recipe[i] for i in [3, 4, 5])


class TestIndexStrings:
    @pytest.mark.parametrize('input, expected', [
        ('1..4', [1, 2, 3, 4]),
        ('8,9,10', [8, 9, 10]),
        ('1', [1])
    ])
    def test_simple(self, input, expected):
        assert parsing.parse_index_string(input, max(expected)) == expected
    @pytest.mark.parametrize('input, expected', [
        ('2,1,3,3,3', [1, 2, 3])
    ])
    def test_sort(self, input, expected):
        assert parsing.parse_index_string(input, max(expected)) == expected
    
    @pytest.mark.parametrize('input, expected', [
        ('1..4;5..8', [1, 2, 3, 4, 5, 6, 7, 8]),
        ('1..1', [1])
    ])
    def test_complex(self, input, expected):
        assert parsing.parse_index_string(input, max(expected) if expected else 1) == expected

    @pytest.mark.parametrize('input, total_len', [
        ('0..0', 1),
        ('4..3', 5),
        ('4..-1', 3),
        ('4..3', 4)
    ])
    def test_vacuous(self, input, total_len):
        # call parse_index_string. if an exception is raised, then the test passes.
        with pytest.raises(Exception):
            parsing.parse_index_string(input, total_len)