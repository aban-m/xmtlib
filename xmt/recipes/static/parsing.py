import yaml

def parse_static_recipe(source):
    if isinstance(source, str):
        return parse_static_recipe(open(source, 'r', encoding='utf-8'))
    return yaml.safe_load(source)

def process_raw(L : list):
    ''' Returns a sorted, duplicate-free version of L'''
    return sorted(list(set(L)))

def parse_index_string(s, total_len):
    ''' Parse an index string, like 0..3;4,5 or 1,-1 '''
    L = []
    if ';' in s: 
        return process_raw(sum(
            [parse_index_string(subs.strip(), total_len) for subs in s.split(';')],
            start = []
        ))
    
    if '..' in s: # a range
        a, b = s.split('..')
        return process_raw(range(int(a)%total_len, int(b)%total_len + 1))
    elif ',' in s: # a comma-separated list
        return process_raw([int(c.strip())%total_len for c in s.split(',')])
    else: # a singleton
        return [int(s)%total_len]
