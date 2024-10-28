from copy import deepcopy
import pytest

from xmt.recipes.storage import MemoryStorage, FileStorage
from xmt.recipes.dynamic.core import DynamicRecipe
from xmt.recipes.static.core import StaticRecipe

@pytest.fixture(scope='module')
def fs():
    return FileStorage(['tests/resources'])

@pytest.fixture(scope='function')
def dyn(fs):
    dyn_env = MemoryStorage()
    dyn_env['basic'] = {
        'metadata': {
            'name': 'Test dynamic recipe',
            'type': 'dynamic',
            'id': 'dyn'
        },
        'include': [],
        'var': [],
        'result': {}
    }
    dyn_env.load_resource = fs.load_resource

    return deepcopy(DynamicRecipe(dyn_env['basic'], dyn_env))

@pytest.fixture(scope='function')
def sta(fs):
    sta_env = MemoryStorage()
    sta_env['basic'] = {
            'metadata': {
                'name': 'Test static recipe',
                'type': 'static',
                'id': 'sta'
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
    sta_env.load_resource = fs.load_resource

    return deepcopy(StaticRecipe(sta_env['basic'], sta_env))