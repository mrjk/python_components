import io
import os
from io import StringIO
import json
import ruamel.yaml



# Setup YAML object
yaml = ruamel.yaml.YAML()
yaml.version = (1, 1)
yaml.default_flow_style = False
# yaml.indent(mapping=3, sequence=2, offset=0)
yaml.allow_duplicate_keys = True
yaml.explicit_start = True



# TODO: add tests
def from_yaml(string):
    "Transform YAML string to python dict"
    return yaml.load(string)


# TODO: add tests
def to_yaml(obj, headers=False):
    "Transform obj to YAML"
    options = {}
    string_stream = StringIO()

    if isinstance(obj, str):
        obj = json.loads(obj)

    yaml.dump(obj, string_stream, **options)
    output_str = string_stream.getvalue()
    string_stream.close()
    if not headers:
        output_str = output_str.split("\n", 2)[2]
    return output_str

# TODO: add tests
def to_json(obj, nice=True):
    "Transform JSON string to python dict"
    if nice:
        return json.dumps(obj, indent=2)
    return json.dumps(obj)


# TODO: add tests
def from_json(string):
    "Transform JSON string to python dict"
    return json.loads(string)


def serialize(obj, fmt="json"):
    "Serialize anything, output json like compatible (destructive)"

    # pylint: disable=unnecessary-lambda
    obj = json.dumps(obj, default=lambda o: str(o), indent=2)

    if fmt in ["yaml", "yml"]:
        # Serialize object in json first
        obj = json.loads(obj)

        # Convert json to yaml
        string_stream = io.StringIO()
        yaml.dump(obj, string_stream)
        output_str = string_stream.getvalue()
        string_stream.close()

        # Remove 2 first lines of output
        obj = output_str.split("\n", 2)[2]

    return obj


def read_file(file):
    "Read file content"
    with open(file, encoding="utf-8") as _file:
        return "".join(_file.readlines())


def write_file(file, content):
    "Write content to file"

    file_folder = os.path.dirname(file)
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)

    with open(file, "w", encoding="utf-8") as _file:
        _file.write(content)

