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

projectPath = os.path.normpath(os.path.join(thisFilePath, "..", "..",'..'))  # Move up to project root
#print('Project path:', projectPath)
dimaPath = os.path.normpath('/'.join([projectPath,'dima']))
#print('DIMA path:', dimaPath)


# Set up project root directory
sys.path.insert(0,projectPath)
sys.path.insert(0,dimaPath)
import dima.src.hdf5_ops as dataOps 
import pipelines.steps.utils as stepUtils
import dima.utils.g5505_utils as utils
import json

def compute_cpc_flags():
    # TODO: ask rob where to find this information.

    return 0

#def compute_diagnostic_variable_flags(data_table, validity_thresholds_dict):
def generate_diagnostic_flags(data_table):
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

    # Implicit input
    validity_thersholds_file = 'pipelines/params/validity_thresholds.yaml'

    validity_thresholds_dict = {}
    try:
        with open(validity_thersholds_file, 'r') as stream:
            validity_thresholds_dict = yaml.load(stream, Loader=yaml.FullLoader)
    except Exception as e:
        
        print(f"Error accessing validation thresholds at: {validity_thersholds_file}")
        return 1
    # Initialize a dictionary to store indicator variables
    indicator_variables = {}

    indicator_variables['t_base'] = data_table['t_base']

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
    new_data_table['flag_any_diagnostic_flag'] = new_data_table.apply(lambda x : any(np.logical_not(x.values)), axis='columns')
    #new_data_table['flag_any_diagnostic'] = new_data_table.apply(
    #    lambda x: np.nan if x.isna().all() else any(x.dropna().values), axis='columns'
    #)
    return new_data_table

def generate_species_flags(data_table : pd.DataFrame , flags_table : pd.DataFrame ):

    """Generate flags for columns in data_table based on flags_table

    Returns
    -------
    _type_
        _description_
    """




    return 0

# all_dat[VaporizerTemp_C >= heater_lower_lim & VaporizerTemp_C <= heater_upper_lim ,flag_heater_auto:="V"]
# all_dat[ABsamp >= AB_lower_lim & ABsamp <= AB_upper_lim ,flag_AB_auto:="V"]
# all_dat[FlowRate_ccs >= flow_lower_lim & FlowRate_ccs <= flow_upper_lim ,flag_flow_auto:="V"]
# all_dat[FilamentEmission_mA >= filament_lower_lim & FilamentEmission_mA <= filament_upper_lim ,flag_filament_auto:="V"]

if __name__ == '__main__':

    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Calibrate species data using calibration factors.")

    parser.add_argument(
        "--flag-type",
        required=True,
        choices=["diagnostics", "species", "cpd"],
        help="Specify the flag type. Must be one of: diagnostics, species, cpd"
    )
    parser.add_argument('data_file', type=str, help="Path to the input HDF5 file containing the data table.")
    parser.add_argument('dataset_name', type=str, help ='Relative path to data_table (i.e., dataset name) in HDF5 file')
    #parser.add_argument('validity_thersholds_file', type=str, help="Path to the input YAML file containing calibration factors.")
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
        datetime_var, datetime_var_format = dataManager.infer_datetime_variable('/'+args.dataset_name)
        dataManager.extract_and_load_dataset_metadata()
        dataset_metadata_df = dataManager.dataset_metadata_df.copy()
        print(dataset_metadata_df.head())

        dataset_name_idx = dataset_metadata_df.index[(dataset_metadata_df['dataset_name']==args.dataset_name).to_numpy()]
        data_table_metadata = dataset_metadata_df.loc[dataset_name_idx,:]
        parent_instrument = data_table_metadata.loc[dataset_name_idx,'parent_instrument'].values[0]
        parent_file = data_table_metadata.loc[dataset_name_idx,'parent_file'].values[0]
        
        dataManager.unload_file_obj()        

    except Exception as e:
        print(f"Error loading input files: {e}")
        exit(1)

    path_to_output_dir, ext = os.path.splitext(args.data_file)

    print('Path to output directory :', path_to_output_dir)



    # Perform calibration

    flag_type = args.flag_type
    try:
        # Define output directory of apply_calibration_factors() step
        suffix = 'flags'
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

        print('Processing script:', processingScriptRelPath)
        print('Output directory:', path_to_output_folder)

        # Compute diagnostic flags based on validity thresholds defined in configuration_file_dict

        if flag_type == 'diagnostics':

            flags_table = generate_diagnostic_flags(data_table) 
            metadata = {'actris_level' : 1, 
                        'processing_script': processingScriptRelPath.replace(os.sep,'/'),
                        'processing_date' : utils.created_at(),
                        'flag_type' : flag_type
                        } 
            
            # Save output tables to csv file and save/or update data lineage record
            filename, ext = os.path.splitext(parent_file)
            path_to_flags_file = '/'.join([path_to_output_folder, f'{filename}_flags.csv'])
            #path_to_calibration_factors_file = '/'.join([path_to_output_folder, f'{filename}_calibration_factors.csv'])
            
            flags_table.to_csv(path_to_flags_file, index=False)
            
            status = stepUtils.record_data_lineage(path_to_flags_file, projectPath, metadata)

            print(f"Flags saved to {path_to_flags_file}")
            print(f"Data lineage saved to {path_to_output_dir}")

        if flag_type == 'species':

            # Save output tables to csv file and save/or update data lineage record
            filename, ext = os.path.splitext(parent_file)
            path_to_flags_file = '/'.join([path_to_output_folder, f'{filename}_flags.csv'])

            variables_set = set(data_table.columns)

            manual_json_flags = []
            csv_flags = []

            # Inspect flags folder
            for filename in os.listdir(path_to_output_folder):
                if any(var in filename and filename.endswith('.json') for var in variables_set):
                    manual_json_flags.append(filename)
                elif filename.endswith('.csv'):
                    csv_flags.append(filename)
            
            if len(csv_flags) == 1:
                flags_table = pd.read_csv(os.path.join(path_to_output_folder, csv_flags[0]))

                if 'flag_any_diagnostic_flag' in flags_table.columns:
                    #renaming_map = {var: f'flag_{var}' for var in data_table.columns}
                    #data_table[renaming_map.keys()] = flags_table['flag_any_diagnostic_flag'].values
                    #data_table.rename(columns=renaming_map, inplace=True)

                    renaming_map = {}
                    for var in data_table.columns:
                        if not datetime_var == var:
                            renaming_map[var] = f'flag_{var}'
                            data_table[var] = pd.Series(flags_table['flag_any_diagnostic_flag'].values)
                    print(renaming_map)
                    data_table.rename(columns=renaming_map, inplace=True)
                print(csv_flags)
            # TODO: validate the code below. I suspect we need to change the flag creation strategy. 
            # First, aggregate manual num flags as one using median maybe and then create a flag for each specie
            # taking into account the existing specifies flags (read csv file and update it if needed)
            for flag_filename in manual_json_flags:
                parts = os.path.splitext(flag_filename)[0].split('_')
                varname = '_'.join(parts[2:])  # Extract variable name from filename
                print(varname)
                if f'flag_{varname}' in data_table.columns:
                    try:
                        with open(os.path.join(path_to_output_folder, flag_filename), 'r') as stream:
                            flag_dict = json.load(stream)

                        t1 = pd.to_datetime(flag_dict.get('startdate'))
                        t2 = pd.to_datetime(flag_dict.get('enddate'))
                        flag_code = flag_dict.get('flag_code', np.nan)  # Default to NaN if missing

                        if pd.isnull(t1) or pd.isnull(t2):
                            continue  # Skip if invalid timestamps

                        if not data_table[datetime_var].is_monotonic_increasing:
                            data_table.sort_values(by=datetime_var, inplace=True)
                            data_table.reset_index(drop=True, inplace=True)

                        t1_idx = abs(data_table[datetime_var] - t1).argmin()
                        t2_idx = abs(data_table[datetime_var] - t2).argmin()

                        data_table.loc[t1_idx:t2_idx, f'flag_{varname}'] = flag_code

                    except (KeyError, ValueError, FileNotFoundError) as e:
                        print(f"Error processing {flag_filename}: {e}")
                        continue

            data_table.to_csv(path_to_flags_file, index=False)


                    # Read json and assign numeric flag to column








    except Exception as e:
        print(f"Error during calibration: {e}")
        exit(1)

