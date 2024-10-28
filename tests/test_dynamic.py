from copy import deepcopy
import pytest

from ..xmt.recipes.dynamic import processor
class TestInclude:
    def test_cyclic_dependency(self, dyn):
        dyn.spec['include'].append({'dynamic': 'basic'})
        try:
            dyn.execute(total=True)
        except RecursionError:
            pytest.fail('Cyclic dependency not caught.')
        except Exception:
            pass
    
    def test_static_include(self, dyn, sta):
        dyn.spec['include'].append({'static': 'dep_sta'})
        dyn.env['dep_sta'] = sta.spec
        dyn.execute(total=True)

        assert 'dep_sta' in dyn.diff
        assert len(dyn.diff['dep_sta']) == 3
    
    def test_dynamic_include(self, dyn, sta):
        dyn2 = deepcopy(dyn)
        dyn2.spec['metadata']['id'] = 'dep'
        dyn2.spec['var'].append({
            'x': {
                'do': 'jinja2',
                'return': 'foo'
            }
        })

        dyn.env['dep'] = dyn2.spec
        dyn.spec['include'].append({'dynamic': 'dep'})
        dyn.execute(total=True)
        dyn2.execute(total=True)

        assert 'dep' in dyn.diff
        assert dyn.diff['dep'] == dyn2.diff
        assert dyn.diff['dep']['x'] == 'foo'
    

class TestVar:
    def test_var_expansion(self, dyn):
        dyn.spec['var'].extend([
            {'x_int': 1},
            {'x_str': 's'},
            {'x_temp': '{{ x_str }}{{ x_int }}'}
        ])

        dyn.execute(total=True)

        assert dyn['x_int'] == 1
        assert dyn['x_str'] == 's'
        assert dyn['x_temp'] == 's1'
    
    def test_var_expansion2(self, dyn):
        dyn.spec['var'].extend([
            {'x_int': 1},
            {'x_str': 's'},
            {'x_temp': '{{ x_str }}{{ x_int }}'}
        ])
        dyn.execute(total=True)

        assert dyn['x_int'] == 1
        assert dyn['x_str'] == 's'
        assert dyn['x_temp'] == 's1'
    
    def test_path_expansion(self, dyn):
        dyn.spec['var'].append(
            {'x': {
                'path': 'testtext.txt'
            }}
        )
        dyn.execute(total=True)

        assert dyn['x'] == 'RAW TEXT'
    
    def test_http_expansion(self, dyn):
        dyn.spec['var'].append(
            {
                'x': {
                    'http': 'https://jsonplaceholder.typicode.com/todos/1'
                }
            }
        )
        dyn.execute(total=True)

        assert isinstance(dyn['x'], dict)
        assert dyn['x'] == {'userId': 1, 'id': 1, 'title': 'delectus aut autem', 'completed': False} # subject to change!
    
class TestExpr:
    def test_jsonpath(self):
        json = {
            'a': 1
        }
        out = processor.jsonpath_query(json, '$.a')
        assert out == 1
    
    def test_jsonpath_deep(self):
        json = {
            'a': [
                {'b': 1}
            ]
        }
        out = processor.jsonpath_query(json, '$.a[0].b')
        assert out == 1
    
    def test_jsonpath_deep2(self):
        json = [
            {
                'a': [{'b': 1}]
            }
        ]
        out = processor.jsonpath_query(json, '$[0].a[0].b')
        assert out == 1
    
    def test_jsonpath_integration(self, dyn):
        dyn.spec['var'].extend([
            {'x': {
                'http': 'https://jsonplaceholder.typicode.com/todos/1',
                'do': 'jsonpath',
                'return': '$.userId'
            }}
        ])
        dyn.execute(total=True)

        assert dyn['x'] == 1
    
