import os
import argparse
import json

# add xmt to the path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xmt.recipes.utils import bootstrap
from xmt.recipes.storage import FileStorage

def main():
    parser = argparse.ArgumentParser(description='Process a recipe.')
    parser.add_argument('recipe_path', type=str, help='Path to the recipe file')
    parser.add_argument('-v', '--variable', type=str, default='', help=\
                        'Variable to return. If not specified, return the result (if dynamic) or content (if static)'
                        'of the recipe. If the value is *, return the entire diff.')
    args = parser.parse_args()

    recipe_path = args.recipe_path
    var = args.variable

    storage = FileStorage([os.path.dirname(recipe_path)])
    recipe_spec = storage.load_recipe(os.path.basename(recipe_path))

    recipe = bootstrap(recipe_spec, storage)
    if recipe.type == 'dynamic':

        diff, result = recipe.execute()
        if not var: print(result)
        elif var == '*': print(json.dumps(diff))
        else:
            try: print(diff[var])
            except KeyError:
                print(f'Variable {var} not found in diff.', file=sys.stderr)

    elif recipe.type == 'static':
        recipe.execute(compile_tags = True)
        if not var:
            print('\n'.join([p['content'] for p in recipe.content]))
        elif var == '*':
            print(json.dumps(recipe.content))
        else:
            try: 
                # check wheter var is an index
                if var.isdigit():
                    print(recipe[int(var) - 1])
                else:
                    col = recipe[var] # get the collection
                    print('\n'.join([p['content'] for p in recipe[col]]))

            except KeyError:
                print(f'Tag {var} not found in the collection.', file=sys.stderr)
    else:
        print(f'Unimplemented recipe type: {recipe.type}.', file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
