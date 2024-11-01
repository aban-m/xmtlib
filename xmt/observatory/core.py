import json
from jsonschema import validate as validate_json
import yaml

class Observer:
    @classmethod
    def from_file(cls, path: str, format = None):
        ''' A convenience method that loads an observer from a YAML or JSON file'''
        if format is None:
            ext = path.split('.')[-1].lower()
            try: format = {'yaml': 'yaml', 'yml': 'yaml', 'json': 'json'}[ext]
            except KeyError: raise ValueError(f'Unknown file extension: {ext}')
        
        schema = None
        with open(path, 'r') as fp:
            if format == 'yaml':
                schema = yaml.safe_load(fp)
            elif format == 'json':
                schema =  json.load(fp)
            else:
                raise ValueError(f'Unknown format: {format}')
        
        return cls(schema)
            
    def __init__(self, schema: dict):
        self.schema = schema
        self.last = None

    def update(self, data: dict, validate: bool = True):
        if validate:
            valid, error = self.validate(data)
            assert valid

        self.last = data

    def validate(self, data: dict):
        ''' Validate the data against the schema. Returns a tuple (valid, error)'''
        try:
            validate_json(instance = data, schema = self.schema)
            return True, None
        except Exception as e:
            return False, e.message