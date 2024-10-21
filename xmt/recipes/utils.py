def without(d : dict, *keys):
    return {k : d[k] for k in d if not k in keys}

def attach(d1, d2): return {**d1, **d2}
