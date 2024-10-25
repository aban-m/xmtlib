import pytest

from ..xmt.recipes.static import parsing
from ..xmt.recipes.static.core import StaticRecipe
from ..xmt.recipes.models import MemoryStorage

@pytest.fixture
def basic_recipe():
    return StaticRecipe(
        {
            'metadata': {
                'name': 'test',
                'type': 'static',
                'content': 'hello world'
            },
            'content': [],
            'tags': {},
            'annotations': {}
        },
        MemoryStorage()
    )




class TestInclude:
    pass

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