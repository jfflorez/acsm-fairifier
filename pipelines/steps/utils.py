import os
import json


def record_data_lineage(path_to_output_file, projectPath, metadata):
    
    path_to_output_dir, output_file = os.path.split(path_to_output_file)
         
    path_to_metadata_file = '/'.join([path_to_output_dir,'data_lineage_metadata.json'])
    # Ensure the file exists
    if not os.path.exists(path_to_metadata_file):
        with open(path_to_metadata_file, 'w') as f:
            json.dump({}, f)  # Initialize empty JSON

    # Read the existing JSON
    with open(path_to_metadata_file, 'r') as metadata_file:
        try:
            json_dict = json.load(metadata_file)
        except json.JSONDecodeError:
            json_dict = {}  # Start fresh if file is invalid

    # Compute relative output file path and update the JSON object
    relpath_to_output_file = os.path.relpath(path_to_output_file, start=projectPath).replace(os.sep, '/')
    json_dict[relpath_to_output_file] = metadata

    # Write updated JSON back to the file
    with open(path_to_metadata_file, 'w') as metadata_file:
        json.dump(json_dict, metadata_file, indent=4)
        
    
    print(f"Metadata for calibrated data saved to {path_to_metadata_file}")
    
    return 0