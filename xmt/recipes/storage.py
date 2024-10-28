import os
import yaml


class Context(dict): pass
class Spec(dict): pass

class StorageException(Exception): pass
class RecipeNotFoundException(StorageException): pass
class CyclicDependencyException(StorageException): pass

class RecipeStorage:
    # make this an abstract class
    def __init__(self):
        pass
    def load_recipe(self, name) -> Spec:
        pass
    def load_resource(self, name):
        raise NotImplementedError

    

class FileStorage(RecipeStorage):
    ''' A file-based storage that stores recipe specifications in files '''
    def __init__(self, paths, append_ext = '.yaml', loader = yaml.safe_load, dumper = yaml.safe_dump):
        ''' Initialize a storage. loader/dumper specify the format (YAML by default)'''
        if isinstance(paths, str): paths = [paths]
        self.paths = paths
        self.loader = loader
        self.dumper = dumper
        self.append_ext = append_ext
    
    def load_recipe(self, name) -> Spec:
        name += self.append_ext
        for path in self.paths:
            full = os.path.join(path, name)
            if os.path.exists(full) and os.path.isfile(full): 
                with open(full, 'r', encoding='utf-8') as fp:
                    return self.loader(fp)
        raise RecipeNotFoundException(f'Could not find {name}.')
    
    def load_resource(self, path, *args, **kwargs) -> str:
        for parent_path in self.paths:
            full = os.path.join(parent_path, path)
            if os.path.exists(full) and os.path.isfile(full): return open(full, *args, **kwargs)
        raise FileNotFoundError(f'Could not find {path}.')

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
    def load_recipe(self, name) -> Spec:
        try: return self[name]
        except KeyError: raise RecipeNotFoundException(f'Could not find {name}.')
    def write(self, name, spec: Spec): self[name] = spec