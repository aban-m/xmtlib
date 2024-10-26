import pytest
from ..xmt.recipes.dynamic.core import DynamicRecipe
from ..xmt.recipes.storage import MemoryStorage, CyclicDependencyException

@pytest.fixture
def basic_recipe():
    spec = {
        'metadata': {
            'name': 'Test recipe',
            'type': 'dynamic',
            'id': 'test_basic'
        },
        'var': {
            
        }
    }

    env = MemoryStorage(basic=spec)
    recipe = DynamicRecipe(spec, env)
    return recipe

