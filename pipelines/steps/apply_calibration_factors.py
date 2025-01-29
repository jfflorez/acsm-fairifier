
import sys, os

try:
    thisFilePath = os.path.abspath(__file__)
    print(thisFilePath)
except NameError:
    print("[Notice] The __file__ attribute is unavailable in this environment (e.g., Jupyter or IDLE).")
    print("When using a terminal, make sure the working directory is set to the script's location to prevent path issues (for the DIMA submodule)")
    #print("Otherwise, path to submodule DIMA may not be resolved properly.")
    thisFilePath = os.getcwd()  # Use current directory or specify a default

dimaPath = os.path.normpath(os.path.join(thisFilePath, "..", "..",'..'))  # Move up to project root
projectPath = os.path.normpath(os.path.join(dimaPath,'..'))
print(dimaPath)
import numpy as np
import pandas as pd
from math import prod  # To replace multiplyall
import argparse
import yaml

# Set up project root directory
#root_dir = os.path.abspath(os.curdir)
#sys.path.append(root_dir)
sys.path.append(dimaPath)

import dima.src.hdf5_ops as dataOps



def apply_calibration_factors(data_table, calibration_factors):
    """
    Calibrates the species data in the given data table using a calibration factor.

    Parameters:
        data_table (pd.DataFrame): The input data table with variables to calibrate.
        calibration_factor (dict): Dictionary containing 'standard' calibration factors
                                   with 'num' and 'den' values as dictionaries of multipliers.

    Returns:
        pd.DataFrame: A new data table with calibrated variables.
    """
    # Make a copy of the input table to avoid modifying the original
    new_data_table = data_table.copy()

    # Initialize a dictionary to rename variables
    variable_rename_dict = {}

    # Loop through the column names in the data table
    for variable_name in new_data_table.select_dtypes(include=["number"]).columns:

        if not variable_name in calibration_factors.keys(): # use standard calibration factor
            # Extract numerator and denominator values
            numerator = prod(value for key, value in calibration_factors['standard']['num'].items())
            denominator = prod(value for key, value in calibration_factors['standard']['den'].items())

        else: # use specifies dependent calibration factor

            #print(variable_name)
            #print([key for key in calibration_factors[variable_name]])
            numerator = prod(value for key, value in calibration_factors[variable_name]['num'].items())
            denominator = prod(value for key, value in calibration_factors[variable_name]['den'].items())

        # Apply calibration to each variable
        new_data_table[variable_name] = new_data_table[variable_name].mul((numerator / denominator))

        # Add renaming entry
        variable_rename_dict[variable_name] = f"{variable_name}_correct"

    # Rename the columns in the new data table
    new_data_table.rename(columns=variable_rename_dict, inplace=True)

    return new_data_table

if __name__ == '__main__':

    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Calibrate species data using calibration factors.")
    parser.add_argument('data_file', type=str, help="Path to the input HDF5 file containing the data table.")
    parser.add_argument('dataset_name', type=str, help ='Relative path to data_table (i.e., dataset name) in HDF5 file')
    parser.add_argument('calibration_file', type=str, help="Path to the input YAML file containing calibration factors.")
    parser.add_argument('output_file', type=str, help="Path to save the output calibrated data as a CSV file.")

    args = parser.parse_args()

    # Load input data and calibration factors
    try:
        #data_table = pd.read_json(args.data_file)

        print(args.data_file)

        dataManager = dataOps.HDF5DataOpsManager(args.data_file)
        dataManager.load_file_obj()
        dataset_name = '/'+args.dataset_name
        data_table = dataManager.extract_dataset_as_dataframe('/'+args.dataset_name)

        dataManager.extract_and_load_dataset_metadata()
        dataset_metadata_df = dataManager.dataset_metadata_df.copy()
        print(dataset_metadata_df.head())

        dataset_name_idx = dataset_metadata_df.index[(dataset_metadata_df['dataset_name']==args.dataset_name).to_numpy()]
        data_table_metadata = dataset_metadata_df.loc[dataset_name_idx,:]
        parent_instrument = data_table_metadata.loc[dataset_name_idx,'parent_instrument'].values[0]
        parent_file = data_table_metadata.loc[dataset_name_idx,'parent_file'].values[0]
        
        dataManager.unload_file_obj()        
        print(args.calibration_file)

        with open(args.calibration_file, 'r') as stream:
            calibration_factors = yaml.load(stream, Loader=yaml.FullLoader)
    except Exception as e:
        print(f"Error loading input files: {e}")
        exit(1)

    path_to_output_dir, ext = os.path.splitext(args.data_file)

    print('Path to output directory :', path_to_output_dir)



    # Perform calibration
    try:

        processingScriptRelPath = os.path.relpath(thisFilePath,start=projectPath)

        print(processingScriptRelPath)

        metadata = {'actris_level' : 1, 'processing_script': processingScriptRelPath.replace(os.sep,'/')}

        path_to_output_file, ext = os.path.splitext('/'.join([path_to_output_dir,parent_instrument,parent_file]))    
        path_to_calibrated_file = ''.join([path_to_output_file, '_calibrated.csv'])
        
        path_tail, path_head = os.path.split(path_to_calibrated_file)
        path_to_metadata_file = '/'.join([path_tail, 'data_lineage_metadata.json'])
        
        print('Path to output file :', path_to_calibrated_file)
        import dima.utils.g5505_utils as utils
        import json
        calibrated_table = apply_calibration_factors(data_table, calibration_factors)  
        metadata['processing_date'] = utils.created_at()
        calibrated_table.to_csv(path_to_calibrated_file, index=False)

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

        # Update the JSON object
        outputfileRelPath = os.path.relpath(path_to_calibrated_file, start=projectPath).replace(os.sep, '/')
        json_dict[outputfileRelPath] = metadata

        # Write updated JSON back to the file
        with open(path_to_metadata_file, 'w') as metadata_file:
            json.dump(json_dict, metadata_file, indent=4)

        print(f"Calibrated data saved to {path_to_calibrated_file}")
        print(f"Metadata for calibrated data saved to {path_to_metadata_file}")
    except Exception as e:
        print(f"Error during calibration: {e}")
        exit(1)