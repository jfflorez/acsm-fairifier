
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


def load_calibration_file(calibration_file):

    # START YAML FILE VALIDATION
    # TODO : create a separate validation function
    with open(calibration_file, 'r') as stream:
        calibration_factors = yaml.load(stream, Loader=yaml.FullLoader)

    # Get path to file where calibrations params are defined
    path_to_calib_params_file = calibration_factors.get("calibration_params", {}).get('path_to_file')

    # Validate
    if not path_to_calib_params_file:
        raise ValueError(f'Invalid yaml file. {calibration_file} must contain "calibration_params" with a valid "path_to_file".')

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
    
def apply_calibration_factors(data_table, datetime_var_name, calibration_file):
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

    calibration_params, calibration_factors = load_calibration_file(calibration_file) 

   
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



    

if __name__ == '__main__':

    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Calibrate species data using calibration factors.")
    parser.add_argument('data_file', type=str, help="Path to the input HDF5 file containing the data table.")
    #parser.add_argument('dataset_name', type=str, help ='Relative path to data_table (i.e., dataset name) in HDF5 file')
    parser.add_argument('calibration_file', type=str, help="Path to the input YAML file containing calibration factors.")
    #parser.add_argument('output_file', type=str, help="Path to save the output calibrated data as a CSV file.")

    args = parser.parse_args()

    # Load input data and calibration factors
    try:
        #data_table = pd.read_json(args.data_file)

        print(args.data_file)

        dataManager = dataOps.HDF5DataOpsManager(args.data_file)
        dataManager.load_file_obj()

        dataManager.extract_and_load_dataset_metadata()
        dataset_metadata_df = dataManager.dataset_metadata_df.copy()


        keywords = ['ACSM_TOFWARE/','ACSM_JFJ_','_timeseries.txt/data_table']
        find_keyword = [all(keyword in item for keyword in keywords) for item in dataset_metadata_df['dataset_name']]

        if sum(find_keyword)!=1:
            input_file_name = '<year>'.join(keywords)
            raise RuntimeError(f'Input file {input_file_name} was neither found nor uniquely identified.')

        dataset_name = dataset_metadata_df['dataset_name'][find_keyword].values[0]
        parent_file = dataset_metadata_df.loc[find_keyword,'parent_file'].values[0]
        parent_instrument = dataset_metadata_df.loc[find_keyword,'parent_instrument'].values[0]

        #dataset_name = '/'+args.dataset_name
        data_table = dataManager.extract_dataset_as_dataframe(dataset_name)
        datetime_var, datetime_format = dataManager.infer_datetime_variable(dataset_name)

        #data_table['t_start_Buf'] = data_table['t_start_Buf'].apply(lambda x : x.decode())

        #dataManager.extract_and_load_dataset_metadata()
        #dataset_metadata_df = dataManager.dataset_metadata_df.copy()
        print(dataset_metadata_df.head())

        #dataset_name_idx = dataset_metadata_df.index[(dataset_metadata_df['dataset_name']==args.dataset_name).to_numpy()]
        #data_table_metadata = dataset_metadata_df.loc[dataset_name_idx,:]
        #parent_instrument = data_table_metadata.loc[dataset_name_idx,'parent_instrument'].values[0]
        #parent_file = data_table_metadata.loc[dataset_name_idx,'parent_file'].values[0]

        print(parent_file)
        
        dataManager.unload_file_obj()        
        print(args.calibration_file)

        if not any(item in args.calibration_file for item in ['.yaml','.yml']):
            raise TypeError(f"Invalid file type. Calibration file {args.calibration_file} needs to be a valid yaml file.")
    except Exception as e:
        print(f"Error loading input files: {e}")
        exit(1)

    path_to_output_dir, ext = os.path.splitext(args.data_file)

    print('Path to output directory :', path_to_output_dir)

    # Count the number of NaT (null) values
    num_nats = data_table[datetime_var].isna().sum()
    # Get the total number of rows
    total_rows = len(data_table)
    # Calculate the percentage of NaT values
    percentage_nats = (num_nats / total_rows) * 100
    print(f"Total rows: {total_rows}")
    print(f"NaT (missing) values: {num_nats}")
    print(f"Percentage of data loss: {percentage_nats:.4f}%")


    # Perform calibration
    try:
        # Define output directory of apply_calibration_factors() step

        suffix = 'processed'
        if len(parent_instrument.split('/')) >= 2:
            instFolder = parent_instrument.split('/')[0]
            category = parent_instrument.split('/')[1]
        else:
            instFolder = parent_instrument.split('/')[0]
            category = ''

        path_to_output_folder, ext = os.path.splitext('/'.join([path_to_output_dir,f'{instFolder}_{suffix}',category]))    
        processingScriptRelPath = os.path.relpath(thisFilePath,start=projectPath)

        if not os.path.exists(path_to_output_folder):
            os.makedirs(path_to_output_folder)

        print(f'Processing script : {processingScriptRelPath}')
        print(f'Output directory : {path_to_output_folder}')

        # Apply calibration factors to input data_table and generate data lineage metadata
        calibration_factor_table, calibrated_table = apply_calibration_factors(data_table, datetime_var, args.calibration_file) #calibration_factors)  
        
        metadata = {'actris_level' : 1, 
                    'processing_script': processingScriptRelPath.replace(os.sep,'/'),
                    'processing_date' : utils.created_at(),
                    'datetime_var': datetime_var}
        
        # Save output tables to csv file and save/or update data lineage record
        filename, ext = os.path.splitext(parent_file)
        path_to_calibrated_file = '/'.join([path_to_output_folder, f'{filename}_calibrated.csv'])
        path_to_calibration_factors_file = '/'.join([path_to_output_folder, f'{filename}_calibration_factors.csv'])
        
        calibrated_table.to_csv(path_to_calibrated_file, index=False)
        calibration_factor_table.to_csv(path_to_calibration_factors_file, index=False)
        
        status = stepUtils.record_data_lineage(path_to_calibrated_file, projectPath, metadata)
        status = stepUtils.record_data_lineage(path_to_calibration_factors_file, projectPath, metadata)

        print('Calibration factors saved to', path_to_calibration_factors_file)
        print(f"Calibrated data saved to {path_to_calibrated_file}")
        print(f"Data lineage saved to {path_to_output_dir}")

    except Exception as e:
        print(f"Error during calibration: {e}")
        exit(1)