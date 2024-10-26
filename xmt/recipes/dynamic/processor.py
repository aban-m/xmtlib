import os.path

import yaml
import json
import re
from jsonpath_ng import parse as parse_jsonpath

from jinja2 import Template

import requests

from xmt.recipes.base import ParsingError
from xmt.recipes.storage import Context, FileStorage

EXT_TYP_MAP = {
    'json': 'json',
    'yaml': 'yaml',
    'yml': 'yaml',
    'txt': 'raw'
}
TYP_EXPR_MAP = {
    'json': 'jsonpath',
    'yaml': 'jinja2',
    'raw': 'jinja2'
}

### PRIMITIVES

def recurse_object(d, func, on):
    if isinstance(d, on):
        return func(d)
    elif isinstance(d, list):
        return [recurse_object(elem, func, on) for elem in d]
    elif isinstance(d, dict):
        return {k: recurse_object(v, func, on) for k, v in d.items()}
    else:
        return d

def recursive_freeze(d): 
    return recurse_object(d, Template, str)
def recursive_render(d, vars : dict):
    def func(d):
        return d.render(vars)
    return recurse_object(d, func, Template)
# convenience wrapper
def interpret(d : dict, context : dict):
    return recursive_render(recursive_freeze(d), context)

### LOADERS
def load_local(path : dict, env : FileStorage):
    target = path['target']
    ext = os.path.splitext(target)[1][1:]
    inferred_type = EXT_TYP_MAP.get(ext, 'raw') # infer type
    received_type = path['type']
    if received_type == 'auto':
        received_type = inferred_type

    full = env.resolve_path(target)
    if received_type == 'binary':
        return open(full, 'rb').read(), inferred_type
    else:
        return open(full, 'r', encoding='utf-8').read(), inferred_type
    
def load_remote(http : dict):
    url = http['target']
    expected_type = http['type']
    http['headers'] = http.get('headers', {})

    data = http.get('data', None)
    if isinstance(data, dict) or isinstance(data, list):
        data = json.dumps(data)
        if not 'Content-Type' in http['headers']:
            http['headers']['Content-Type'] = 'application/json'

    resp = requests.request(
        http.get('method', 'GET'),
        url = url,
        headers = http['headers'],
        data = data
    )

    # infer type
    type_header = resp.headers['Content-Type']
    inferred_type = expected_type
    if 'application/json' in type_header:
        inferred_type = 'json'
    # (should add more type inference)

    return resp.content.decode('utf-8'), inferred_type

### PROCESSING
def process(func: str, fetched, ret, state: Context):
    if func == 'jsonpath':
        return jsonpath_query(fetched, Template(ret).render(**state))
    elif func == 'regex':
        return re.sub(fetched[0], ret, fetched[1])
    elif func == 'nothing':
        return ret
    elif func == 'jinja2':
        assert not fetched, 'jinja2 does not support multiple inputs'
        return Template(ret).render(**state)


def jsonpath_query(json, jpath):
    out = [match.value for match in parse_jsonpath(jpath).find(json)]
    if len(out) == 1:
        return out[0]
    else:
        return out
    
### CASTING
def cast(type, raw):
    if type == 'json':
        return json.loads(raw)
    elif type == 'yaml':
        return yaml.safe_load(raw)
    elif type == 'raw' or type is None:
        return raw
    else:
        raise ValueError(f'Unrecognized type {type}.')
