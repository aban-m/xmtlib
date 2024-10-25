import yaml

def process_raw(L : list):
    ''' Returns a sorted, duplicate-free version of L'''
    return sorted(list(set(L)))

def _process_index(i, total_len):
    if i == 0: raise ValueError('Zero value is not allowed; indexing starts from 1.')
    if i < 0: i = total_len + i
    if i > total_len:
        raise ValueError('Index must be <= total length.')
    return i
def _process_endpoints(start, end, total_len):
    start = _process_index(start, total_len)
    end = _process_index(end, total_len)

    if start > end: raise ValueError('Start endpoint must be <= end endpoint.')
    if end > total_len: raise ValueError('End endpoint must be <= total length.')

    return start, end

def parse_index_string(s, total_len):
    ''' Parse an index string, like 0..3;4,5 or 1,-1 '''
    total_len += 1 # fixes the 0 case, and makes it inclusive

    # recursive branch
    if ';' in s: 
        return process_raw(sum(
            [parse_index_string(subs.strip(), total_len) for subs in s.split(';')],
            start = []
        ))
    
    # simple branch
    if '..' in s: # a range
        a, b = s.split('..')
        a, b = _process_endpoints(int(a.strip()), int(b.strip()), total_len)
        return [i for i in range(a, b+1)]
    
    elif ',' in s: # a comma-separated list
        return process_raw([_process_index(int(c.strip()), total_len) for c in s.split(',')])
    else: # a singleton
        return [_process_index(int(s.strip()), total_len)]
    