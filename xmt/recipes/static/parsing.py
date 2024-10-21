import yaml

def parse_static_recipe(source):
    if isinstance(source, str):
        return parse_static_recipe(open(source, 'r', encoding='utf-8'))
    return yaml.safe_load(source)

def parse_index_string(s, total_len):
    ''' Parse an index string, like 0..3;4,5 or 1,-1 '''
    L = []
    if ';' in s: return sum(
        [parse_index_string(subs.strip(), total_len) for subs in s.split(';')],
        start = []
    )
    
    if '..' in s:
        a, b = s.split('..')
        return list(range(int(a)%total_len, int(b)%total_len + 1))
    elif ',' in s:
        return [int(c)%total_len for c in s.split(',')]
    else: return [int(s)%total_len]
