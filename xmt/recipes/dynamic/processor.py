import os.path

import yaml
import json
from jsonpath_ng import parse as parse_jsonpath

from jinja2 import Template

import requests

EXT_MAP = {
    'json': 'json',
    'yaml': 'yaml',
    'yml': 'yaml',
    'txt': 'raw'
}

### PRIMITIVES

def recurse_object(d, func, on):
    if isinstance(d, on): return func(d)
    elif isinstance(d, list): return [recurse_object(elem, func, on) for elem in d]
    elif isinstance(d, dict):
        return {k: recurse_object(v, func, on) for k, v in d.items()}
    else:
        return d

def recursive_freeze(d): return recurse_object(d, Template, str)
def recursive_render(d, vars : dict):
    func = lambda d: d.render(vars)
    return recurse_object(d, func, Template)
# convenience wrapper
def interpret(d : dict, context : dict):
    return recursive_render(recursive_freeze(d), context)

### LOADING
def load(dec, env):
    path = dec.get('path', '')
    if not path: return None
    typ = dec.get('type', None)
    if path.lower().startswith('http') or 'http' in dec:
        return load_remote(path, typ, dec.get('http', {}))
    return load_local(path, typ, env)

def load_local(path, typ, env):
    path = env.lookup(path)
    ext = os.path.splitext(path)[1].lower()
    if typ is None: typ = EXT_MAP.get(ext, 'raw')

    with open(path, 'r', encoding='utf-8') as fp:
        if typ == 'json': return json.load(fp)
        elif typ == 'yaml': return yaml.safe_load(fp)
        elif typ == 'raw':
            return fp.read()
        else:
            raise ValueError('Unrecognized type.')

def load_remote(path, typ, http_params, return_bytes=False):
    method = http_params.get('method', 'GET')
    data = http_params.get('data', None)
    headers = http_params.get('headers', {})

    req_type = headers.get('Content-Type', '')
    
    if not req_type:
        # determining the request type from the data
        if isinstance(data, dict) or isinstance(data, list): req_type = 'application/json'
    headers['Content-Type'] = req_type
    
    if 'application/json' in req_type and not isinstance(data, str):
        data = json.dumps(data)
        
    # now we are ready!
    resp = requests.request(method, url = path, data = data, headers = headers)

    if return_bytes: return resp.content # simply return the raw 
    else:
        if 'json' in resp.headers['Content-Type']: return json.loads(resp.content.decode('utf-8'))
        else: return resp.content.decode('utf-8')


### SPECIALTIES!
def jsonpath_query(json, jpath):
    out = [match.value for match in parse_jsonpath(jpath).find(json)]
    if len(out) == 1: return out[0]
    
### EXPRESSIONS
def resolve_expression(expr, ret, state, var_name):
    content = state[var_name]

    if expr == 'raw':
        return ret
    elif expr == 'jsonpath':
        return jsonpath_query(content, ret)
    elif expr == 'jinja2':
        return Template(ret).render(**state)
    elif expr == 'regex':
        return re.sub(
            ret['pattern'],
            ret['template'],
            content
        )
    

