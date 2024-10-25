import os
import io
import yaml

class Context(dict): pass
class Spec(dict): pass

    # def lookup(self, name):
    #     assert not os.path.split(name)[0], 'Can only look up files with given names'
    #     for path in self.paths:
    #         full = os.path.join(path, name)
    #         if os.path.exists(full) and os.path.isfile(full): return full
    #     raise FileNotFoundError(f'Could not find {name}.')

class StorageException(Exception): pass
class RecipeNotFoundException(StorageException): pass
class CyclicDependencyException(StorageException): pass

class RecipeStorage:
    # make this an abstract class
    def __init__(self):
        pass
    def load(self, name) -> Spec:
        pass

    

class FileStorage(RecipeStorage):
    ''' A file-based storage that stores recipe specifications in files '''
    def __init__(self, paths, loader = yaml.safe_load, dumper = yaml.safe_dump):
        ''' Initialize a storage. loader/dumper specify the format (YAML by default)'''
        if isinstance(paths, str): paths = [paths]
        self.paths = paths
        self.loader = loader
        self.dumper = dumper
    
    def load(self, name) -> Spec:
        for path in self.paths:
            full = os.path.join(path, name)
            if os.path.exists(full) and os.path.isfile(full): 
                with open(full, 'r', encoding='utf-8') as fp:
                    return self.loader(fp)
        raise RecipeNotFoundException(f'Could not find {name}.')
    
    def write(self, name, spec):
        with open(name, 'w', encoding='utf-8') as fp:
            self.dumper(spec, fp)
    
    @classmethod
    def current(cls):
        return cls(['.'])

class MemoryStorage(RecipeStorage, dict):
    ''' A memory-storage that stores recipe specifications directly '''
    def __init__(self, **data):
        super().__init__(**data)
    def load(self, name) -> Spec:
        try: return self[name]
        except KeyError: raise RecipeNotFoundException(f'Could not find {name}.')
    def write(self, name, spec: Spec): self[name] = spec