import sys, os
import re

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

import numpy as np
import pandas as pd
from dima.instruments.readers.nasa_ames_reader import read_nasa_ames_as_dict
from pipelines.steps.utils import compute_uncertainty_estimate

def main(path_to_data_file, base_column_names : list):

    """Adjust the error or uncertainty columns of data table, where data table is available
     in input nas file and by specifying a list of columns to adjust.

    Parameters:
    ------------
    path_to_data_file (str) : Path to nas file
    base_column_names (list) : list of column names 

    Raises
    ------
    RuntimeError
        _description_
    ValueError
        _description_
    ValueError
        _description_
    ValueError
        _description_
    RuntimeError
        _description_
    """


    if not path_to_data_file.endswith('.nas'):
        raise RuntimeError(f'Invalid file extension. The input file {path_to_data_file} must be a .nas file.')

    # Read and extract data
    idr_dict = read_nasa_ames_as_dict(path_to_data_file)
    header_metadata_dict = idr_dict['attributes_dict']

    # Locate data table
    dataset = None
    for d in idr_dict['datasets']:
        if d['name'] == 'data_table':
            dataset = d
    if dataset is None:
        raise ValueError("Dataset named 'data_table' not found.")

    data_table = dataset['data']  # structured numpy array
    df = pd.DataFrame(data_table)

    if any(col not in df.columns for col in base_column_names):
        raise ValueError(f"Base column '{col}' not found in dataset.")
    
    # filter out columns with name starting in 'err_'
    base_column_names_cleaned = [col for col in base_column_names if not col.startswith('err_')]


    # Read original lines from file
    with open(path_to_data_file, 'rb') as file:
        raw_lines = file.readlines()

    header_length = header_metadata_dict['header_length']
    
    

    for col in base_column_names_cleaned:
        
        data_table_lines = []
        base_column_name = col

        err_column = f"err_{base_column_name}"
        if err_column not in df.columns:
            raise ValueError(f"Column '{err_column}' not found in dataset.")

        # Apply callback to base column

        err_index = data_table.dtype.names.index(err_column)
        # Iterate through data table lines
        cnt = 0
        for line_idx in range(len(raw_lines)):
            if line_idx >= header_length - 1:
                line = raw_lines[line_idx]
                fields = list(re.finditer(rb'\S+', line))

                if err_index < len(fields):
                    match = fields[err_index]
                    original_bytes = match.group()
                    original_str = original_bytes.decode('utf-8')

                    # Skip column header or fill values
                    clean_original_str = original_str.strip().replace('.', '')
                    if err_column in original_str: 
                        data_table_lines.append(line)
                        continue

                    # Decimal precision
                    decimals = len(original_str.split('.')[1]) if '.' in original_str else 0

                    try:
                        original_err = float(original_str)
                        if not (clean_original_str and all(c == '9' for c in clean_original_str)):
                            additional_term = df.loc[cnt, base_column_name]
                            updated_value = compute_uncertainty_estimate(additional_term, original_err)
                        else: # if original value is missing, then keep the same
                            updated_value = original_err
                    except Exception as e:
                        raise RuntimeError(f"Error calculating updated value on line {line_idx}: {e}")

                    # Preserve width and precision
                    start, end = match.span()
                    width = end - start
                    formatted_str = f"{updated_value:.{decimals}f}"

                    if len(formatted_str) > width:
                        print(f"Warning: formatted value '{formatted_str}' too wide for field of width {width} at line {line_idx}. Value may be truncated.")

                    formatted_bytes = formatted_str.rjust(width).encode('utf-8')
                    new_line = line[:start] + formatted_bytes + line[end:]
                    data_table_lines.append(new_line)
                    cnt += 1
        # update raw lines
        for line_idx in range(header_length - 1, len(raw_lines)):
            raw_lines[line_idx] = data_table_lines[line_idx - header_length + 1]        

    # Reconstruct the file
    processed_lines = (
        header_metadata_dict['raw_header_part1'] +
        header_metadata_dict['raw_header_part2'] +
        header_metadata_dict['raw_header_part3'] +
        data_table_lines
    )

    # Write updated content to file
    with open(path_to_data_file, 'wb') as f:
        for line in processed_lines:
            decoded = line.decode('utf-8').rstrip('\n')
            f.write((decoded + '\n').encode('utf-8'))


if __name__ == '__main__':
    path_to_data_file = os.path.normpath(os.path.join(
        'data', 'CH0002G.20240201010000.20250521123253.aerosol_mass_spectrometer.chemistry_ACSM.pm1_non_refractory.7w.1h.CH02L_Aerodyne_ToF-ACSM_092.CH02L_Aerodyne_ToF-ACSM_PAY.lev2.nas'
    ))
    main(path_to_data_file, base_column_name='Org')
