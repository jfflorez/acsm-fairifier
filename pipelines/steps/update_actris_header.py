import sys, os

try:
    thisFilePath = os.path.abspath(__file__)
    print(thisFilePath)
except NameError:
    print("[Notice] The __file__ attribute is unavailable in this environment (e.g., Jupyter or IDLE).")
    print("When using a terminal, make sure the working directory is set to the script's location to prevent path issues (for the DIMA submodule)")
    #print("Otherwise, path to submodule DIMA may not be resolved properly.")
    thisFilePath = os.getcwd()  # Use current directory or specify a default

projectPath = os.path.normpath(os.path.join(thisFilePath, "..", "..",'..'))  # Move up to project root

if projectPath not in sys.path:
    sys.path.insert(0,projectPath)

import yaml
import re
import argparse

def flatten_yaml(data, sep=', '):
    """Flatten only nested values in the YAML dict by joining dict values into strings."""
    flat = {}
    for k, v in data.items():
        if isinstance(v, dict):
            # Join all values in the dict as a single string with separator
            flat[k] = sep.join(str(val) for val in v.values())
        else:
            flat[k] = v
    return flat

def load_template(path):
    with open(path, 'r') as f:
        return f.read()

def load_yaml(path):
    with open(path, 'r') as f:
        metadata = yaml.safe_load(f)
        actris_metadata = {
            'originator': metadata['originator'],
            'submitter': metadata['submitter'],
            'station': metadata['station'],
        }
        actris_metadata['originator_name'] = metadata['originator'].get('name', '')
        return flatten_yaml(actris_metadata)

def resolve_project_path():
    try:
        thisFilePath = os.path.abspath(__file__)
    except NameError:
        thisFilePath = os.getcwd()
    return os.path.normpath(os.path.join(thisFilePath, "..", "..", ".."))

def fill_placeholders(template, data):
    def replacer(match):
        key = match.group(1)
        return str(data.get(key, f"${{{key}}}"))  # Leave placeholder if not found
    return re.sub(r'\$\{(\w+)\}', replacer, template)

def main(data_descriptor_path, dry_run = None):


    if not os.path.exists(data_descriptor_path):
        raise FileNotFoundError(f'Data descriptor not found at: {data_descriptor_path}')

    metadata = load_yaml(data_descriptor_path)
    print(metadata)

    station = metadata.get('station', None)
    if not station:
        raise RuntimeError(
            f'"station" is not defined in {data_descriptor_path}. '
            'Make sure you specify it as station: "JFJ" or station: "PAY"'
        )

    # Define header paths
    header_template_map = {
        "JFJ": "pipelines/actris_header/JFJ_ACSM_017.actris_header",
        "PAY": "pipelines/actris_header/PAY_ACSM_092.actris_header",
    }

    header_uptate_map = {
        "JFJ": "third_party/acsmProcessingSoftware/src/cfg/actris_header/JFJ_ACSM_017.actris_header",
        "PAY": "third_party/acsmProcessingSoftware/src/cfg/actris_header/PAY_ACSM_092.actris_header",
    }

    if station not in header_template_map:
        raise RuntimeError(f'Station "{station}" is not supported. Choose from: {list(header_template_map)}')

    #projectPath = resolve_project_path()
    header_path = os.path.join(projectPath, header_template_map[station])

    if not os.path.exists(header_path):
        raise FileNotFoundError(f"Header template not found at: {header_path}")

    print(f"Using template: {header_path}")
    template_str = load_template(header_path)
    filled = fill_placeholders(template_str, metadata)

    if dry_run:
        out_path = "output.test.ext"
        print("[DRY RUN] Target header was not overwritten.")
    else:
        out_path = os.path.join(projectPath, header_uptate_map[station])
        print("[LIVE RUN] Target header will be updated.")
        print(f"Writing to: {out_path}")

    
    

    with open(out_path, 'w') as f:
        f.write(filled)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fill ACTRIS header from metadata descriptor.")
    parser.add_argument(
        "data_descriptor_path",
        help="Path to metadata YAML (data descriptor)"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Do not overwrite original template. Write output to 'output.test.ext'."
    )
    args = parser.parse_args()

    data_descriptor_path = args.data_descriptor_path
    dry_run = args.dry_run
    main(data_descriptor_path,dry_run )