import os
import os.path

class Context(dict): pass
class Spec(dict): pass

class Environment:
    @classmethod
    def current(self):
        return Environment(os.getcwd())
    
    def __init__(self, *paths):
        self.paths = paths
    def lookup(self, name):
        assert not os.path.split(name)[0], 'Can only look up files with given names'
        for path in self.paths:
            full = os.path.join(path, name)
            if os.path.exists(full) and os.path.isfile(full): return full
        raise FileNotFoundError(f'Could not find {name}.')
