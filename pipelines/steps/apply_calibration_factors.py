
import sys, os

try:
    thisFilePath = os.path.abspath(__file__)
    print('File path:',thisFilePath)
except NameError:
    print("[Notice] The __file__ attribute is unavailable in this environment (e.g., Jupyter or IDLE).")
    print("When using a terminal, make sure the working directory is set to the script's location to prevent path issues (for the DIMA submodule)")
    #print("Otherwise, path to submodule DIMA may not be resolved properly.")
    thisFilePath = os.getcwd()  # Use current directory or specify a default

projectPath = os.path.normpath(os.path.join(thisFilePath, "..", "..",'..'))  # Move up to project root
#print('Project path:', projectPath)
dimaPath = os.path.normpath('/'.join([projectPath,'dima']))
#print('DIMA path:', dimaPath)


# Set up project root directory
sys.path.insert(0,projectPath)
sys.path.insert(0,dimaPath)


#import importlib.util
#print("Checking if projectPath exists:", os.path.exists(projectPath))
#if os.path.exists(projectPath):
#    print("Contents of dimaPath:", os.listdir(projectPath))
#print("Checking if Python can find 'dima':", importlib.util.find_spec("dima"))

import numpy as np
import pandas as pd
from math import prod  # To replace multiplyall
import argparse
import yaml

import dima.src.hdf5_ops as dataOps
import dima.utils.g5505_utils as utils
import pipelines.steps.utils as stepUtils
from pipelines.steps.utils import generate_error_dataframe
from pipelines.steps.utils import load_project_yaml_files

def compute_calibration_factors(data_table, datetime_var_name, calibration_params, calibration_factors):
    """
    Computes calibration factor values for variables (excluding the time variable) in data_table.
    
    Parameters
    ----------
    data_table : pd.DataFrame
        Data table containing time-series data.
    datetime_var_name : str
        Name of the datetime column in data_table.
    calibration_params : dict
        Dictionary containing calibration interval details.
    calibration_factors : dict
        Dictionary specifying numerator and denominator variables for calibration.

    Returns
    -------
    pd.DataFrame
        DataFrame containing computed calibration factors for each variable.
    """
    
    calibration_factors_dict = {}    

    #calibration_factors_dict = {datetime_var_name : data_table[datetime_var_name].to_numpy()}

    

    # Create table to store the factors and parameters 
    column_params = [datetime_var_name]
    column_factors = []
    for name in list(calibration_params['default_params'].keys()) + list(calibration_factors['variables'].keys()):
        if '_tofware' in name: 
            column_params.append(name.replace('_tofware','_correct'))
        else:
            column_factors.append(f'factor_{name}')
    print(datetime_var_name, data_table[datetime_var_name].size, len(column_params+column_factors))
    tmp_df = pd.DataFrame(data=np.full(shape=(data_table[datetime_var_name].size, len(column_params)+len(column_factors)), fill_value=np.nan),columns=column_params+column_factors)

    tmp_df[datetime_var_name] = data_table[datetime_var_name].to_numpy()
    
    # print(tmp_df.head())

    for variable_name in calibration_factors['variables']:

        
        print(variable_name)

        #tmp = np.full(shape=data_table[datetime_var_name].shape, fill_value=np.nan)

        
        for interval_idx, interval_params in calibration_params['calibration_intervals'].items():  # Fixed typo
            t1 = pd.to_datetime(interval_params['start_datetime'], format = "%Y-%m-%d %H-%M-%S")
            t2 = pd.to_datetime(interval_params['end_datetime'], format = "%Y-%m-%d %H-%M-%S")

            t1_idx = abs(data_table[datetime_var_name] - t1).argmin()
            t2_idx = abs(data_table[datetime_var_name] - t2).argmin()

            if t1_idx <= t2_idx:
                numerator = prod(interval_params[key] for key in calibration_factors['variables'][variable_name]['num'])
                denominator = prod(interval_params[key] for key in calibration_factors['variables'][variable_name]['den'])

                if denominator == 0:
                    raise ZeroDivisionError(f"Denominator is zero for '{variable_name}' in interval {t1} - {t2}")

                tmp_df.loc[t1_idx:t2_idx, f'factor_{variable_name}'] = numerator / denominator
                for param in column_params:
                    if param in interval_params:
                        tmp_df.loc[t1_idx:t2_idx, param] = interval_params[param]   

            else:
                raise ValueError(f"Invalid calibration interval: start_datetime {t1} must be before end_datetime {t2}")

        #calibration_factors_dict[f'factor_{variable_name}'] = tmp

    #return pd.DataFrame(data=calibration_factors_dict)
    return tmp_df


def load_calibration_file(calibration_factors_file):

    # Load and validate calibration factors structure. TODO: Make sure load_project_yaml_files implements YAML FILE VALIDATION. 
    filename = os.path.split(calibration_factors_file)[1]
    calibration_factors = load_project_yaml_files(projectPath,filename) 

    # Get path to file where calibrations params are defined
    path_to_calib_params_file = calibration_factors.get("calibration_params", {}).get('path_to_file')
    path_to_calib_params_file = os.path.normpath(os.path.join(projectPath,path_to_calib_params_file))

    # Validate
    if not path_to_calib_params_file:
        raise ValueError(f'Invalid yaml file. {calibration_factors_file} must contain "calibration_params" with a valid "path_to_file".')

    if not os.path.exists(path_to_calib_params_file):
        raise FileNotFoundError(f'Calibration parameters file not found: {path_to_calib_params_file}')
    
    with open(path_to_calib_params_file, 'r') as stream:
        calibration_params = yaml.load(stream, Loader=yaml.FullLoader)
        
    #calibration_params = calibration_params['calibration_intervals']['interval_1']
    #for key in calibration_params['calibration_intervals']['interval_1']:
    #    if not key in['start_datetime','end_datetime']:
    #        calibration_params[key] = calibration_params['calibration_intervals']['interval_1'][key]
    
    # Get variable to calibration factors dictionary
    #calibration_factors = calibration_dict.get('variables',{})
    #calibration_factors['calibration_params'].update(calibration_params)
    # TODO: perform a validation step before computing factors
    ### END YAML FILE VALIDATION

    return calibration_params, calibration_factors
    
def apply_calibration_factors(data_table, datetime_var_name, calibration_factors_file : str = 'pipelines/params/calibration_factors.yaml'):
    """
    Calibrates the species data in the given data table using a calibration factor.

    Parameters
    ----------
        data_table (pd.DataFrame): The input data table with variables to calibrate.
        calibration_file (string): Calibration YAML file with a dictionary containing calibration factors for each variable in
                                   the data_table, where factors are specified in terms of their
                                   'num' and 'den' values as dictionaries of multipliers.

    Returns
    -------
        pd.DataFrame: A new data table with calibrated variables.
    """
    # Make a copy of the input table to avoid modifying the original
    new_data_table = data_table.copy()

    calibration_params, calibration_factors = load_calibration_file(calibration_factors_file)

   
    calibration_factor_table = compute_calibration_factors(new_data_table, 
                                                           datetime_var_name, 
                                                           calibration_params, 
                                                           calibration_factors)
    
    # Initialize a dictionary to rename variables
    variable_rename_dict = {}
    # Loop through the column names in the data table
    for variable in new_data_table.select_dtypes(include=["number"]).columns:

        if variable in calibration_factors['variables'].keys(): # use standard calibration factor
            
            # Apply calibration to each variable
            new_data_table[variable] = new_data_table[variable].mul(calibration_factor_table[f'factor_{variable}'])

            # Add renaming entry
            variable_rename_dict[variable] = f"{variable}_correct"

        else: # use specifies dependent calibration factor
            print(f'There is no calibration factors for variable {variable}. The variable will remain the same.')



    # Rename the columns in the new data table
    new_data_table.rename(columns=variable_rename_dict, inplace=True)

    return calibration_factor_table, new_data_table


def main(data_file, calibration_file):
    """Main function for processing the data with calibration."""
    # Load input data and calibration factors
    try:
        print(f"Opening data file: {data_file} using src.hdf5_ops.HDF5DataOpsManager().")
        dataManager = dataOps.HDF5DataOpsManager(data_file)
        dataManager.load_file_obj()

        dataManager.extract_and_load_dataset_metadata()
        dataset_metadata_df = dataManager.dataset_metadata_df.copy()

        keywords = ['ACSM_TOFWARE/', 'ACSM_JFJ_', '_timeseries.txt/data_table']
        find_keyword = [all(keyword in item for keyword in keywords) for item in dataset_metadata_df['dataset_name']]

        if sum(find_keyword) != 1:
            input_file_name = '<year>'.join(keywords)
            raise RuntimeError(f'Input file {input_file_name} was neither found nor uniquely identified.')

        dataset_name = dataset_metadata_df['dataset_name'][find_keyword].values[0]
        parent_file = dataset_metadata_df.loc[find_keyword, 'parent_file'].values[0]
        parent_instrument = dataset_metadata_df.loc[find_keyword, 'parent_instrument'].values[0]

        data_table = dataManager.extract_dataset_as_dataframe(dataset_name)
        datetime_var, datetime_format = dataManager.infer_datetime_variable(dataset_name)
        print(dataset_metadata_df.head())
        print(parent_file)
        print(calibration_file)

    except Exception as e:
        print(f"Error loading input files: {e}")
    finally:
        dataManager.unload_file_obj()
        print(f'Closing data file: {data_file} to unlock the file.')

    # Count NaT values and calculate percentage
    num_nats = data_table[datetime_var].isna().sum()
    total_rows = len(data_table)
    percentage_nats = (num_nats / total_rows) * 100
    print(f"Total rows: {total_rows}")
    print(f"NaT (missing) values: {num_nats}")
    print(f"Percentage of data loss: {percentage_nats:.4f}%")

    # Perform calibration
    try:
        suffix = 'processed'
        if len(parent_instrument.split('/')) >= 2:
            instFolder = parent_instrument.split('/')[0]
            category = parent_instrument.split('/')[1]
        else:
            instFolder = parent_instrument.split('/')[0]
            category = ''

        path_to_output_dir, _ = os.path.splitext(data_file)
        path_to_output_folder = os.path.join(path_to_output_dir, f"{instFolder}_{suffix}", category)
        if not os.path.exists(path_to_output_folder):
            os.makedirs(path_to_output_folder)

        print(f"Output directory: {path_to_output_folder}")

        # Apply calibration factors to input data_table and generate data lineage metadata
        calibration_factor_table, calibrated_table = apply_calibration_factors(data_table, datetime_var, calibration_file)
        calibrated_table_err = generate_error_dataframe(calibrated_table, datetime_var)

        suffix_to_dataframe_dict = {
            'calibrated.csv': calibrated_table,
            'calibrated_err.csv': calibrated_table_err,
            'calibration_factors.csv': calibration_factor_table
        }

        metadata = {
            'actris_level': 1,
            'processing_script': os.path.relpath(__file__, start=os.getcwd()),
            'processing_date': utils.created_at(),
            'datetime_var': datetime_var
        }

        # Save output tables to CSV and record data lineage
        filename, _ = os.path.splitext(parent_file)
        if not _:
            filename += '.csv'

        for suffix, data_table in suffix_to_dataframe_dict.items():
            path_to_output_file = os.path.join(path_to_output_folder, f'{filename}_{suffix}')
            try:
                data_table.to_csv(path_to_output_file, index=False)
                print(f"Saved {filename}_{suffix} to {path_to_output_folder}")
            except Exception as e:
                print(f"Failed to save {path_to_output_file} due to: {e}")
                continue

            # Record data lineage
            metadata['suffix'] = suffix
            stepUtils.record_data_lineage(path_to_output_file, os.getcwd(), metadata)

    except Exception as e:
        print(f"Error during calibration: {e}")
        exit(1)

if __name__ == '__main__':
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Calibrate species data using calibration factors.")
    parser.add_argument('data_file', type=str, help="Path to the input HDF5 file containing the data table.")
    #parser.add_argument('dataset_name', type=str, help ='Relative path to data_table (i.e., dataset name) in HDF5 file')
    parser.add_argument('calibration_file', type=str, help="Path to the input YAML file containing calibration factors.")
    #parser.add_argument('output_file', type=str, help="Path to save the output calibrated data as a CSV file.")
    args = parser.parse_args()

    if not any(item in args.calibration_file for item in ['.yaml', '.yml']):
        raise TypeError(f"Invalid file type. Calibration file {args.calibration_file} needs to be a valid YAML file.")

    main(args.data_file, args.calibration_file)


    

