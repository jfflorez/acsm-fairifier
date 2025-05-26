import os
import json, yaml
import numpy as np
import pandas as pd

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
    #grelpath_to_output_file = os.path.relpath(path_to_output_file, start=projectPath).replace(os.sep, '/')
    json_dict[output_file] = metadata

    # Write updated JSON back to the file
    with open(path_to_metadata_file, 'w') as metadata_file:
        json.dump(json_dict, metadata_file, indent=4)
        
    
    print(f"Metadata for calibrated data saved to {path_to_metadata_file}")
    
    return 0

def get_metadata(path_to_file):

    path, filename = os.path.split(path_to_file)

    path_to_metadata = None
    for item in os.listdir(path):
        if 'metadata.json' in item:
            path_to_metadata = os.path.normpath(os.path.join(path,item))
    metadata = {}
    if path_to_file:
        with open(path_to_metadata,'r') as stream:
            metadata = json.load(stream)
    
        metadata = metadata.get(filename,{})

    return metadata

import numpy as np

import numpy as np

def generate_missing_value_code(max_val, num_decimals):
    """
    Generate the largest all-9s missing value that can be represented exactly by float.
    Caps total digits to 16 to avoid rounding.

    Args:
        max_val (float): Largest expected valid value in the column.
        num_decimals (int): Number of decimal places to preserve.

    Returns:
        float: The missing value code.
    """
    MAX_SIGNIFICANT_DIGITS = 16

    # Calculate order of magnitude (roughly digits before decimal)
    order = int(np.floor(np.log10(max_val))) + 2 if max_val > 0 else 2

    # Cap total digits at 16 to avoid float rounding
    total_digits = order + num_decimals
    if total_digits > MAX_SIGNIFICANT_DIGITS:
        # Reduce integer digits first to keep decimals if possible
        int_digits = max(MAX_SIGNIFICANT_DIGITS - num_decimals, 1)
        dec_digits = min(num_decimals, MAX_SIGNIFICANT_DIGITS - int_digits)
    else:
        int_digits = order
        dec_digits = num_decimals

    # Construct the missing code string
    if dec_digits > 0:
        int_part = '9' * int_digits
        dec_part = '9' * dec_digits
        missing_code_str = f"{int_part}.{dec_part}"
    else:
        missing_code_str = '9' * int_digits

    missing_code = float(missing_code_str)

    return missing_code

def compute_uncertainty_estimate(x,x_err):
    return ((0.5*x_err)**2+(0.5*x)**2)**0.5


def generate_error_dataframe(df: pd.DataFrame, datetime_var):
    """
    Generates an error DataFrame by filling numeric 'correct' columns with a missing value code.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame containing numerical columns.
    datetime_var : str
        Name of the datetime column to retain.

    Returns
    -------
    pd.DataFrame
        DataFrame with error values based on missing value codes.
    """
    df_numeric = df.select_dtypes(include=np.number)

    err_df_columns = []
    err_df_values = []

    # Correct way to filter columns containing 'correct'
    correct_cols = [col for col in df_numeric.columns if 'correct' in col]

    for col in correct_cols:
        missing_value_code = generate_missing_value_code(df[col].max(skipna=True), 4)
        err_df_values.append(missing_value_code)
        err_df_columns.append(f"{col}_err")

    # Fix np.matmul usage and reshape err_df_values correctly
    err_matrix = np.tile(np.array(err_df_values), (len(df),1)) # np.ones((len(df), len(err_df_values))) * np.array(err_df_values)

    df_err = pd.DataFrame(data=err_matrix, columns=err_df_columns)

    # Ensure datetime_var exists in df before assignment
    if datetime_var in df.columns:
        df_err[datetime_var] = df[datetime_var].values
    else:
        raise ValueError(f"Column '{datetime_var}' not found in DataFrame")

    return df_err

import numpy as np
import pandas as pd

def metadata_dict_to_dataframe(metadata: dict, shape: tuple):
    """
    Converts a metadata dictionary into a repeated data table.

    Parameters
    ----------
    metadata : dict
        Dictionary containing metadata where keys are column names and values are repeated across rows.
    shape : tuple
        Shape of the output DataFrame (rows, columns). The number of columns must match the length of `metadata`.

    Returns
    -------
    pd.DataFrame
        DataFrame with metadata values repeated according to the specified shape.
    """
    # Ensure shape is valid (rows, columns)
    rows, cols = shape

    if cols != len(metadata):
        raise ValueError(f"Shape mismatch: {cols} columns expected, but metadata has {len(metadata)} keys.")

    # Extract metadata values and reshape them properly
    values = np.array(list(metadata.values())).reshape((1,cols))

    # Tile the values to match the desired shape
    data_table = np.tile(values, (rows, 1))

    # Create DataFrame with correct column names
    df = pd.DataFrame(data=data_table, columns=list(metadata.keys()))

    return df

def resolve_project_path():
    try:
        thisFilePath = os.path.abspath(__file__)
    except NameError:
        thisFilePath = os.getcwd()
    return os.path.normpath(os.path.join(thisFilePath, "..", "..", ".."))

def load_project_yaml_files(projectPath : str, filename : str):

    allowed_filenames = ['acsm_to_ebas.yaml', 'calibration_params.yaml', 'calibration_factors.yaml', 'limits_of_detection.yaml', 'station_params.yaml', 'validity_thresholds.yaml', 'campaignDescriptor.yaml']

    if not filename in allowed_filenames:
        raise ValueError(f'Invalid filename : {filename}. The filename should be selected from the following list {allowed_filenames}.')
    
    filename_to_relpath  = {"acsm_to_ebas.yaml":"pipelines/dictionaries/acsm_to_ebas.yaml",
                         "calibration_params.yaml":"pipelines/params/calibration_params.yaml",
                         "calibration_factors.yaml" : "pipelines/params/calibration_factors.yaml",
                         "limits_of_detection.yaml":"pipelines/params/limits_of_detection.yaml",
                         "station_params.yaml":"pipelines/params/station_params.yaml",
                         "validity_thresholds.yaml":"pipelines/params/validity_thresholds.yaml",
                         "campaignDescriptor.yaml":"campaignDescriptor.yaml"}

    # Implicit input
    if filename_to_relpath.get(filename,None):
        dict_file = os.path.normpath(os.path.join(projectPath,filename_to_relpath[filename]))

    output_dict = {}
    try:
        with open(dict_file, 'r') as stream:
            output_dict = yaml.load(stream, Loader=yaml.FullLoader)
    except Exception as e:
        
        print(f'Error loading {dict_file}: {e}')
        return {}
    
    return output_dict