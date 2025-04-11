import os
import sys
import yaml
import argparse

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

def load_yaml(filepath):

    """
        Load YAML data from a given file path.
    """
    with open(filepath, 'r') as file:
        try:
            data = yaml.full_load(file)
            return data
        except yaml.YAMLError as e:
            print(f"Error reading YAML file {filepath}: {e}")
            return None

def compare_structure(src_data, dest_data):

    """
        Compare two YAML structures.
        Check that both have the same keys and that the type of each value matches.
        Returns True if the structures are identical, otherwise False.
    """

    if type(src_data) is not dict or type(dest_data) is not dict:
        # For this use-case, we only compare dictionaries.
        return False

    # Compare keys: make sure src_data keys is a subset of the keys of dest_data
    if not set(src_data.keys()) <= set(dest_data.keys()): # equivalent to not all(key in dest_data.keys() for key in src_data.keys()):
        return False
    
    # Compare the type of values for each key
    for key in src_data:
        if type(src_data[key]) is not type(dest_data[key]):
            return False
        # If the value itself is a dictionary, we recursively check its structure.
        if isinstance(src_data[key], dict):
            if not compare_structure(src_data[key], dest_data[key]):
                return False

    return True

def sync_yaml_files(src_filepath, dest_filepath):
    
    """
        Synchronize YAML file from src to dest if structures match.
    """

    src_yaml = load_yaml(src_filepath)
    dest_yaml = load_yaml(dest_filepath)    

    if src_yaml is None or dest_yaml is None:
        print(f"Skipping synchronization for {os.path.basename(src_filepath)} due to YAML loading errors.")
        return
    
    # Update the destination values with the source values if structure yaml file structure matches (i.e., the src is a subset of the dest)
    if compare_structure(src_yaml, dest_yaml):
        # Preserve structure present in dest_yaml (current set of parameters) but it is missing in src_yaml 
        # by adding to the src_yaml only the keys that are present in dest_yaml but missing in src_yaml
        if set(src_yaml.keys()) <= set(dest_yaml.keys()):
            for key, value in dest_yaml.items():
                if key not in src_yaml:
                    src_yaml[key] = value

        # Replace the entire content of dest_yaml with src_yaml
        # If a more nuanced merging is needed, modify this logic.
        dest_yaml = src_yaml
        # Write the updated YAML back to the destination file.
        with open(dest_filepath, 'w') as dest_file:
            yaml.safe_dump(dest_yaml, dest_file, default_flow_style=False)
        print(f"Synchronized: {os.path.basename(src_filepath)}")
    else:
        print(f"Structures do not match for {os.path.basename(src_filepath)}. Skipping synchronization.")

def main(path_to_data_file, instrument_folder):
    
    
    src_folder = os.path.normpath(os.path.join(os.path.splitext(path_to_data_file)[0],instrument_folder))

    # Define the source (param) and destination (destional) folders.
    #src_folder = "param"
    dest_folder = '/'.join([projectPath,'pipelines/params'])

    # Check if folders exist.
    if not os.path.isdir(src_folder):
        print(f"Source folder '{src_folder}' does not exist.")
        return
    if 'params' not in os.listdir(src_folder):        
        print(f"Folder params/ not found in source folder {src_folder}. ")
        return
    if not os.path.isdir(dest_folder):
        print(f"Destination folder '{dest_folder}' does not exist.")
        return

    # Get list of files in source folder.
    # We assume we only need to process .yaml files.
    src_folder = os.path.normpath(os.path.join(src_folder,'params'))
    for filename in os.listdir(src_folder):
        if filename.endswith(".yaml"):
            src_filepath = os.path.join(src_folder, filename)
            dest_filepath = os.path.join(dest_folder, filename)

            # Proceed only if the destination file exists.
            if os.path.exists(dest_filepath):
                sync_yaml_files(src_filepath, dest_filepath)
            else:
                print(f"Destination YAML file not found for: {filename}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Update data chain parameters with input directory.")
    parser.add_argument(
        "path_to_data_file",
        type=str,
        help="Path to hdf5 file"
    )
    parser.add_argument(
        "instrument_folder", type=str,
        help="Enter a valid instrument folder e.g., ACSM_TOFwARE/<year>"
    )
    args = parser.parse_args()

    path_to_data_file = args.path_to_data_file
    instrument_folder = args.instrument_folder

    main(path_to_data_file, instrument_folder)


