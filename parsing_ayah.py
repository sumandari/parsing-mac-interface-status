import ast
import json
import sys
from pathlib import Path


def readline_as_dict(f):
    line = f.readline().strip()
    line = json.loads(line)
    if not line:
        return None
    result = ast.literal_eval(line)
    if not isinstance(result, dict):
        raise Exception(
            "The contents format is not correct! "
            "Please check your file."
        )
    return result


def parsing(file):
    print("Start parsing...")
    parsed_file = Path(file)
    if not parsed_file.is_file():
        print('File does not exist!')
        exit(1)
    with open(parsed_file, 'r') as f:
        lines = f.readlines()
        print('')


if __name__ == "__main__":
    args = sys.argv
    if len(args) == 1:
        print('Enter your filename!')
        exit(1)
    parsing(args[1])
