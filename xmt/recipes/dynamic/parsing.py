import yaml

def parse_dynamic_recipe(source):
    if isinstance(source, str):
        source = open(source)
    return yaml.safe_load(source)
