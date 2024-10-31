def process_raw(L: list):
    """Returns a duplicate-free version of L"""
    return list(set(L))         # will be sorted later. 

def _process_index(i, total_len):
    if i == 0:
        raise ValueError("Zero value is not allowed; indexing starts from 1.")
    if i < 0:
        i = total_len + i + 1
    if i > total_len:
        raise ValueError("Index must be <= total length.")
    return i


def _process_endpoints(start, end, total_len):
    start = _process_index(start, total_len)
    end = _process_index(end, total_len)

    if start > end:
        raise ValueError("Start endpoint must be <= end endpoint.")
    if end > total_len:
        raise ValueError("End endpoint must be <= total length.")

    return start, end


def parse_index_string(s, total_len):
    """Parse an index string, like 0..3;4,5 or 1,-1"""
    # recursive branch
    if ";" in s:
        return process_raw(
            sum(
                [parse_index_string(subs.strip(), total_len) for subs in s.split(";")],
                start=[],
            )
        )

    # simple branch
    if ".." in s:  # a range
        a, b = s.split('..')
        
        if not a: a = '1'
        if not b: b = str(total_len)
        
        if b.startswith('/'): b = f'{total_len}/{b[1:]}'
        if '/' not in b: b += '/1'

        b, step = b.split('/')
        step = int(step)
        assert step > 0

        a, b = _process_endpoints(int(a.strip()), int(b.strip()), total_len)
        step = int(step)

        return list(range(a, b + 1, step))

    elif "," in s:  # a comma-separated list
        return process_raw([
            _process_index(int(c.strip()), total_len) for c in s.split(",")
        ])
    else:  # a singleton
        return [_process_index(int(s.strip()), total_len)]
