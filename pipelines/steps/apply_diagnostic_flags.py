import sys, os

try:
    thisFilePath = os.path.abspath(__file__)
    print(thisFilePath)
except NameError:
    print("[Notice] The __file__ attribute is unavailable in this environment (e.g., Jupyter or IDLE).")
    print("When using a terminal, make sure the working directory is set to the script's location to prevent path issues (for the DIMA submodule)")
    #print("Otherwise, path to submodule DIMA may not be resolved properly.")
    thisFilePath = os.getcwd()  # Use current directory or specify a default

import numpy as np
import pandas as pd
import argparse

import yaml, json

dimaPath = os.path.normpath(os.path.join(thisFilePath, "..", "..",'..'))  # Move up to project root
projectPath = os.path.normpath(os.path.join(dimaPath,'..'))
print(dimaPath)
sys.path.append(dimaPath)
import dima.src.hdf5_ops as dataOps 
import pipelines.steps.utils as stepUtils
import dima.utils.g5505_utils as utils
import json

def compute_diagnostic_variable_flags(data_table, validity_thresholds_dict):
    """
    Create indicator variables that check whether a particular diagnostic variable is within
    pre-specified/acceptable limits, which are defined by `variable_limits`.

    Parameters:
        data_table (pd.DataFrame): The input data table with variables to calibrate.
        variable_limits (dict): Dictionary mapping diagnostic-variables to their limits, e.g.,
            {
              'ABsamp': {
                  'lower_lim': {'value': 20000, 'description': "not specified yet"},
                  'upper_lim': {'value': 500000, 'description': "not specified yet"}
              }
            }
         
    Returns:
        pd.DataFrame: A new data table with calibrated variables, containing the original columns
                      and additional indicator variables, representing flags.
    """

    # Initialize a dictionary to store indicator variables
    indicator_variables = {}

    # Loop through the column names in the data table
    for diagnostic_variable in data_table.columns:
        print(diagnostic_variable)
        # Skip if the diagnostic variable is not in variable_limits
        if diagnostic_variable not in validity_thresholds_dict['validity_thresholds']['variables']:
            print(f'Diagnostic variable {diagnostic_variable} has not defined limits in {validity_thresholds_dict}.')
            continue

        # Get lower and upper limits for diagnostic_variable from variable limits dict
        variable_ranges = validity_thresholds_dict['validity_thresholds']['variables'][diagnostic_variable]
        lower_lim = variable_ranges['lower_lim']
        upper_lim = variable_ranges['upper_lim']
        
        # Create an indicator variable for the current diagnostic variable
        tmp = data_table[diagnostic_variable]
        indicator_variables['flag_'+diagnostic_variable] = ((tmp >= lower_lim) & (tmp <= upper_lim)).to_numpy()

    # Add indicator variables to the new data table
    new_data_table = pd.DataFrame(indicator_variables)

    return new_data_table


# all_dat[VaporizerTemp_C >= heater_lower_lim & VaporizerTemp_C <= heater_upper_lim ,flag_heater_auto:="V"]
# all_dat[ABsamp >= AB_lower_lim & ABsamp <= AB_upper_lim ,flag_AB_auto:="V"]
# all_dat[FlowRate_ccs >= flow_lower_lim & FlowRate_ccs <= flow_upper_lim ,flag_flow_auto:="V"]
# all_dat[FilamentEmission_mA >= filament_lower_lim & FilamentEmission_mA <= filament_upper_lim ,flag_filament_auto:="V"]

if __name__ == '__main__':

    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Calibrate species data using calibration factors.")
    parser.add_argument('data_file', type=str, help="Path to the input HDF5 file containing the data table.")
    parser.add_argument('dataset_name', type=str, help ='Relative path to data_table (i.e., dataset name) in HDF5 file')
    parser.add_argument('calibration_file', type=str, help="Path to the input YAML file containing calibration factors.")
    #parser.add_argument('output_file', type=str, help="Path to save the output calibrated data as a CSV file.")

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
        path_to_calibrated_file = ''.join([path_to_output_file, '_flags.csv'])
        
        path_tail, path_head = os.path.split(path_to_calibrated_file)
        path_to_metadata_file = '/'.join([path_tail, 'data_lineage_metadata.json'])
        
        print('Path to output file :', path_to_calibrated_file)

        print(calibration_factors.keys())
        calibrated_table = compute_diagnostic_variable_flags(data_table, calibration_factors)  
        metadata['processing_date'] = utils.created_at()
        calibrated_table.to_csv(path_to_calibrated_file, index=False)

        status = stepUtils.record_data_lineage(path_to_calibrated_file, projectPath, metadata)



        print(f"Calibrated data saved to {path_to_calibrated_file}")
        print(f"Metadata for calibrated data saved to {path_to_metadata_file}")
    except Exception as e:
        print(f"Error during calibration: {e}")
        exit(1)