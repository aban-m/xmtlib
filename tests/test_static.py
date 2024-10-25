import pytest

from ..xmt.recipes.static import parsing

@pytest.mark.parametrize('index_string, value', [
    ('1..4', [1, 2, 3, 4]),
    ('3 .. 7; 1..  5', [1, 2, 3, 4, 5, 6, 7]),
    ('4,  1, 2', [1, 2, 4])
])
def test_index_strings(index_string, value):
    assert parsing.parse_index_string(index_string, max(value)) == value

