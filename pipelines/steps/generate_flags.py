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
dimaPath = os.path.normpath('/'.join([projectPath,'dima']))
#print('Project path:', projectPath)
#print('DIMA path:', dimaPath)


# Set up project root directory
sys.path.insert(0,projectPath)
sys.path.insert(0,dimaPath)
import dima.src.hdf5_ops as dataOps 
import pipelines.steps.utils as stepUtils
import dima.utils.g5505_utils as utils
import json
from pipelines.steps.utils import load_project_yaml_files, get_metadata
from math import floor

path_to_ebas_dict = os.path.normpath(os.path.join(projectPath,'app/flags/ebas_dict.yaml'))
with open(path_to_ebas_dict ,'r') as stream:
    ebas_dict = yaml.safe_load(stream)
    flags_dict = ebas_dict['flags']
    flag_ranking = ebas_dict['flag_ranking']


# Vectorized function for getting the rank of a flag
def get_rank(flag):
    return flag_ranking.get(flag, -10)  # Default rank is NaN for unknown flags

# Vectorized function for reconciling flags
def reconcile_flags(data_table, flag_code, t1_idx, t2_idx, numflag_columns):
    # Extract the relevant subtable
    sub_table = data_table.loc[t1_idx:t2_idx, numflag_columns].copy()

    # Compute ranks of current values
    current_ranks = np.vectorize(get_rank)(sub_table.values)

    # Handle flag_code: broadcast scalar or reshape array
    if np.isscalar(flag_code):
        flag_code_values = np.full(sub_table.shape, flag_code)
        flag_code_ranks = np.full(sub_table.shape, get_rank(flag_code))
    else:
        # Convert to NumPy array and ensure correct shape
        flag_code_array = np.asarray(flag_code)
        if flag_code_array.ndim == 1:
            # Assume it's one flag per row — broadcast across columns
            flag_code_values = np.tile(flag_code_array[:, None], (1, len(numflag_columns)))
            flag_code_ranks = np.vectorize(get_rank)(flag_code_values)
        else:
            # Full 2D matrix
            flag_code_values = flag_code_array
            flag_code_ranks = np.vectorize(get_rank)(flag_code_array)

        # Validate shape match
        if flag_code_values.shape != sub_table.shape:
            raise ValueError(f"Shape mismatch: expected {sub_table.shape}, got {flag_code_values.shape}")

    # Reconcile values based on rank comparison
    new_values = np.where(current_ranks < flag_code_ranks, flag_code_values, sub_table.values)

    # Assign reconciled values back
    data_table.loc[t1_idx:t2_idx, numflag_columns] = new_values.astype(np.int64)

    return data_table

def generate_cpc_flags(data_table, datetime_var: str = 'start_time'):
    # TODO: ask Rob where to find this information.
    required_variables = ['start_time', 'end_time', 'st_y', 'ed_y', 'p_int', 'T_int', 'conc', 'numflag']

    # Optionally check if required variables exist in data_table
    # Uncomment if you want to enforce the check:
    # if not all(var in data_table.columns for var in required_variables):
    #     raise ValueError("Some required variables are missing from the data_table.")

    # Select only datetime and numflag columns
    flags_table = data_table.loc[:, [datetime_var, 'numflag']].copy()
    print(flags_table.head())

    # Multiply numflag by 100 and floor it
    flags_table['numflag'] = flags_table['numflag'].apply(lambda x: floor(x * 1000))

    flags_table.rename(columns={'numflag':'numflag_cpc'}, inplace=True)

    default_value = flags_dict[999]
    flags_table['flag_conc'] = flags_table['numflag_cpc'].copy().values
    flags_table['flag_conc'] = flags_table['flag_conc'].apply(lambda x : flags_dict.get(x,default_value)['validity']=='I')

    return flags_table


#def compute_diagnostic_variable_flags(data_table, validity_thresholds_dict):
def generate_diagnostic_flags(data_table, validity_thresholds_dict):
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


    
    # Define binary to ebas flag code map
    # Specify labeling function to create numbered EBAS flags. It maps a column indicator,
    # marking a time interval in which a particular flagging event occurred.  
    binary_to_ebas_code = {False : 0, True : 456}


    # Initialize a dictionary to store indicator variables
    indicator_variables = {}

    indicator_variables['t_base'] = data_table['t_base']

    # Loop through the column names in the data table
    for diagnostic_variable in data_table.columns:
        #print(diagnostic_variable)
        # Skip if the diagnostic variable is not in variable_limits
        if diagnostic_variable not in validity_thresholds_dict['validity_thresholds']['variables']:
            print(f'Unspecified validity thresholds for variable {diagnostic_variable}. If needed, update pipelines/params/validity_thresholds.yaml accordingly.')
            continue

        # Get lower and upper limits for diagnostic_variable from variable limits dict
        variable_ranges = validity_thresholds_dict['validity_thresholds']['variables'][diagnostic_variable]
        lower_lim = variable_ranges['lower_lim']
        upper_lim = variable_ranges['upper_lim']
        
        # Create an indicator variable for the current diagnostic variable
        tmp = data_table[diagnostic_variable]
        indicator_variables['flag_'+diagnostic_variable] = np.logical_not(((tmp >= lower_lim) & (tmp <= upper_lim)).to_numpy())
        indicator_variables['numflag_'+diagnostic_variable] = np.array([binary_to_ebas_code[entry] for entry in indicator_variables['flag_'+diagnostic_variable]], dtype=np.int64)

    # Add indicator variables to the new data table
    new_data_table = pd.DataFrame(indicator_variables)

    aggr_func = lambda x : max(x.values)
    new_data_table['numflag_any_diagnostic_flag'] = new_data_table.loc[:,['numflag_' in col for col in new_data_table.columns]].aggregate(aggr_func,axis='columns')

    aggr_func = lambda x : np.nan if x.isna().all() else any(x.dropna().values)
    new_data_table['flag_any_diagnostic_flag'] = new_data_table.loc[:,['flag_' in col for col in new_data_table.columns]].aggregate(aggr_func, axis='columns')
    #new_data_table['flag_any_diagnostic_flag'] = new_data_table.apply(lambda x : any(np.logical_not(x.values)), axis='columns')
    #new_data_table['flag_any_diagnostic'] = new_data_table.apply(
    #    lambda x: np.nan if x.isna().all() else any(x.dropna().values), axis='columns'
    #)
    return new_data_table

from scipy.interpolate import interp1d

def generate_species_flags(data_table : pd.DataFrame, calib_param_dict : dict, flagsFolderPath, datetime_var : str = 't_start_Buf'):

    """Generate flags for columns in data_table based on flags_table

    Returns
    -------
    _type_
        _description_
    """


    print('Retreiving species to be flagged ...')
    predefined_species = calib_param_dict.get('variables',{}).get('species',[])
    print(f'Species to be flagged are: {predefined_species}. If needed, update pipelines/params/calibration_params.yaml')

    if not predefined_species:
        raise RuntimeError("Undefined species. Input argument 'calib_param_dict' must contain a 'variables' : {'species' : ['example1',...,'examplen']} ")

    manual_json_flags, csv_flags = get_flags_from_folder(flagsFolderPath)
    #print(manual_json_flags,csv_flags)

    if csv_flags:

        # Loop over CSV files in the flags folder
        for filename in csv_flags:
            filePath = os.path.join(flagsFolderPath, filename)
            fileMetadataDict = get_metadata(filePath)
            flag_datetime_var = fileMetadataDict['datetime_var']

            flags_table = pd.read_csv(filePath)

            # Ensure datetime type
            data_table[datetime_var] = pd.to_datetime(data_table[datetime_var])
            flags_table[flag_datetime_var] = pd.to_datetime(flags_table[flag_datetime_var])

            if 'numflag_any_diagnostic_flag' in flags_table.columns:
                # Sort for interpolation
                flags_table_sorted = flags_table.sort_values(flag_datetime_var)

                # Pre-convert datetimes to int64 for interpolation
                flag_times_int = flags_table_sorted[flag_datetime_var].astype(np.int64)
                data_times_int = data_table[datetime_var].astype(np.int64)

                # Nearest-neighbor interpolator
                flag_interp_func = interp1d(
                    flag_times_int,
                    flags_table_sorted['numflag_any_diagnostic_flag'],
                    kind='nearest',
                    bounds_error=False,
                    fill_value='extrapolate'
                )

                # Interpolated flags
                interpolated_flags = flag_interp_func(data_times_int)

                # Define which columns to flag
                required = lambda var: var != datetime_var and var in predefined_species
                renaming_map = {var: f'numflag_{var}' for var in data_table.columns if required(var)}
                variables = list(renaming_map.keys())

                # Assign flags to those columns
                for var in variables:
                    data_table[var] = interpolated_flags

                data_table.rename(columns=renaming_map, inplace=True)
                
            elif 'numflag_cpc' in flags_table.columns:
                # Sort for interpolation
                flags_table_sorted = flags_table.sort_values(flag_datetime_var)

                # Pre-convert datetimes to int64 for interpolation
                flag_times_int = flags_table_sorted[flag_datetime_var].values.astype(np.int64)
                data_times_int = data_table[datetime_var].values.astype(np.int64)

                # Nearest-neighbor interpolator
                flag_interp_func = interp1d(
                    flag_times_int,
                    flags_table_sorted['numflag_cpc'],
                    kind='nearest',
                    bounds_error=False,
                    fill_value='extrapolate'
                )

                # Interpolated flags
                interpolated_cpc_flags = flag_interp_func(data_times_int)
                    

    else:
        raise FileNotFoundError("Automated diagnostic flag .csv not found. Hint: Run pipelines/step/generate_flags.py <campaignFile.h5> --flag-type diagnostics.")


    numflag_columns = [col for col in data_table.columns if 'numflag_' in col]

    data_table = reconcile_flags(data_table, interpolated_cpc_flags, 0, interpolated_cpc_flags.size, numflag_columns)

    #print(numflag_columns)
    for flag_filename in manual_json_flags:
        #print(flag_filename)
        parts = os.path.splitext(flag_filename)[0].split('_')
        varname = '_'.join(parts[2:])  # Extract variable name from filename
        
        #if f'flag_{varname}' in data_table.columns:
        try:
            # Load manually generate flag
            with open(os.path.join(flagsFolderPath, flag_filename), 'r') as stream:
                flag_dict = json.load(stream)                    

            t1 = pd.to_datetime(flag_dict.get('startdate'))
            t2 = pd.to_datetime(flag_dict.get('enddate'))
            flag_code = flag_dict.get('flag_code', np.nan)  # Default to NaN if missing

            if pd.isnull(t1) or pd.isnull(t2):
                continue  # Skip if invalid timestamps

            if not data_table[datetime_var].is_monotonic_increasing:
                data_table.sort_values(by=datetime_var, inplace=True)
                data_table.reset_index(drop=True, inplace=True)

            t1_idx = int(abs(data_table[datetime_var] - t1).argmin())
            t2_idx = int(abs(data_table[datetime_var] - t2).argmin())
            #print(flag_code)
            #for col in data_table.columns:
                
            #    if 'numflag_' in col:
            #        print(col)

            data_table = reconcile_flags(data_table, flag_code, t1_idx, t2_idx, numflag_columns)
        except (KeyError, ValueError, FileNotFoundError) as e:
            print(f"Error processing {flag_filename}: {e}")
            continue



    # Binarize flags for streamlined visualization of invalid and valid regions
    binary_flag_columns = []
    default_code = 999 # EBAS missing measurement unspecified reason
    default_value = flags_dict[default_code]  # fallback definition for unknown flags

    # Convert them to integer type (handling NaNs if needed)
    data_table[numflag_columns] = data_table[numflag_columns].fillna(default_code).astype(int)

    for numflag_var in numflag_columns:
        flag_var = numflag_var.replace('numflag_', 'flag_')
        binary_flag_columns.append(flag_var)

        # Apply validity check: True if flag is 'I' (invalid)
        data_table[flag_var] = data_table[numflag_var].apply(
            lambda x: flags_dict.get(x, default_value).get('validity') == 'I'
        )


    return data_table.loc[:, [datetime_var] + numflag_columns + binary_flag_columns]





# all_dat[VaporizerTemp_C >= heater_lower_lim & VaporizerTemp_C <= heater_upper_lim ,flag_heater_auto:="V"]
# all_dat[ABsamp >= AB_lower_lim & ABsamp <= AB_upper_lim ,flag_AB_auto:="V"]
# all_dat[FlowRate_ccs >= flow_lower_lim & FlowRate_ccs <= flow_upper_lim ,flag_flow_auto:="V"]
# all_dat[FilamentEmission_mA >= filament_lower_lim & FilamentEmission_mA <= filament_upper_lim ,flag_filament_auto:="V"]

def main(data_file, flag_type):
    # Open data file and load dataset associated with flag_type : either diagnostics or species
    try:
        dataManager = dataOps.HDF5DataOpsManager(data_file)
        dataManager.load_file_obj()

        base_name = '/ACSM_TOFWARE'
        if '/ACSM_TOFWARE' not in dataManager.file_obj:
            dataManager.unload_file_obj()
            print(f'Invalid data file: {data_file}. Missing instrument folder ACSM_TOFWARE.')
            raise ImportError(f'Instrument folder "/ACSM_TOFWARE" not found in data_file : {data_file}')
        

        
        dataManager.extract_and_load_dataset_metadata()
        dataset_metadata_df = dataManager.dataset_metadata_df.copy()
        STATION_ABBR = load_project_yaml_files(projectPath,'campaignDescriptor.yaml')['station_abbr']
        # Find dataset associated with diagnostic channels
        if flag_type == 'diagnostics':
           keywords = [f'ACSM_{STATION_ABBR}_','_meta.txt/data_table']
           find_keyword = [all(keyword in item for keyword in keywords) for item in dataset_metadata_df['dataset_name']]

        if flag_type == 'species':
           keywords = [f'ACSM_{STATION_ABBR}_','_timeseries.txt/data_table']
           find_keyword = [all(keyword in item for keyword in keywords) for item in dataset_metadata_df['dataset_name']]

        if flag_type == 'cpc':
           keywords = ['cpc.particle_number_concentration.aerosol.', f'CH02L_TSI_3772_{STATION_ABBR}.CH02L_CPC.lev1.nas']
           find_keyword = [all(keyword in item for keyword in keywords) for item in dataset_metadata_df['dataset_name']]

        # Specify source dataset to be extracted from input hdf5 data file
        columns = ['dataset_name','parent_file','parent_instrument']
        dataset_name, parent_file, parent_instrument = tuple(dataset_metadata_df.loc[find_keyword,col] for col in columns) 
        print(':)')
        if not (dataset_name.size == 1):
            raise ValueError(f'{flag_type} file is not uniquely identifiable: {parent_file}')
        else: 
            dataset_name = dataset_name.values[0]
            parent_file = parent_file.values[0]
            parent_instrument = parent_instrument.values[0]

        data_table = dataManager.extract_dataset_as_dataframe(dataset_name)
        datetime_var, datetime_var_format = dataManager.infer_datetime_variable(dataset_name)
        

        # Count the number of NaT (null) values
        num_nats = data_table[datetime_var].isna().sum()
        # Get the total number of rows
        total_rows = len(data_table)
        # Calculate the percentage of NaT values
        percentage_nats = (num_nats / total_rows) * 100
        print(f"Total rows: {total_rows}")
        print(f"NaT (missing) values: {num_nats}")
        print(f"Percentage of data loss: {percentage_nats:.4f}%")
        
        dataManager.unload_file_obj()        

    except Exception as e:        
        print(f"Error loading input files: {e}")
        exit(1)
    finally:
        dataManager.unload_file_obj() 



    print('Starting flag generation.')
    try:
        path_to_output_dir, ext = os.path.splitext(data_file)
        print('Path to output directory :', path_to_output_dir)
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
            #validity_thresholds_dict = load_parameters(flag_type)
            validity_thresholds_dict = load_project_yaml_files(projectPath, "validity_thresholds.yaml")
            flags_table = generate_diagnostic_flags(data_table, validity_thresholds_dict)           

        if flag_type == 'species':  
            #calib_param_dict = load_parameters(flag_type)     
            calib_param_dict = load_project_yaml_files(projectPath, "calibration_params.yaml")     
            flags_table = generate_species_flags(data_table,calib_param_dict,path_to_output_folder,datetime_var)
        if flag_type == 'cpc':    
            print(':D')
            flags_table = generate_cpc_flags(data_table, datetime_var)
                
        metadata = {'actris_level' : 1, 
            'processing_script': processingScriptRelPath.replace(os.sep,'/'),
            'processing_date' : utils.created_at(),
            'flag_type' : flag_type,
            'datetime_var': datetime_var
            } 
        
        # Save output tables to csv file and save/or update data lineage record
        filename, ext = os.path.splitext(parent_file)
        path_to_flags_file = '/'.join([path_to_output_folder, f'{filename}_flags.csv'])
        #path_to_calibration_factors_file = '/'.join([path_to_output_folder, f'{filename}_calibration_factors.csv'])
        
        flags_table.to_csv(path_to_flags_file, index=False)        
        status = stepUtils.record_data_lineage(path_to_flags_file, projectPath, metadata)

        print(f"Flags saved to {path_to_flags_file}")
        print(f"Data lineage saved to {path_to_output_folder}")
        
        #flags_table.to_csv(path_to_flags_file, index=False)


                    # Read json and assign numeric flag to column

    except Exception as e:
        print(f"Error during calibration: {e}")
        exit(1)


def get_flags_from_folder(flagsFolderPath):
    # Get current state of flags folder, which will condition the species flagging
    manual_json_flags = []
    csv_flags = []
    
    # Loop through all files in the flags folder
    for folderitem in os.listdir(flagsFolderPath):
        
        # Skip system-level metadata JSON file
        if all([folderitem.endswith('.json'), 'metadata' in folderitem]):
            continue
        
        # Identify manual flag JSON files with 'flag_<number>_<variablename>.json' format
        if folderitem.startswith('flag') and folderitem.endswith('.json'):
            manual_json_flags.append(folderitem)
        # Identify CSV flag files
        elif folderitem.endswith('.csv') and '_flags' in folderitem:
            csv_flags.append(folderitem)
    
    # Return the lists of manual flag JSON files and CSV flag files
    return manual_json_flags, csv_flags

if __name__ == '__main__':

    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Generate flags for diagnostics and species variables.")

    parser.add_argument(
        "--flag-type",
        required=True,
        choices=["diagnostics", "species", "cpc"],
        help="Specify the flag type. Must be one of: diagnostics, species, cpc"
    )
    parser.add_argument('data_file', type=str, help="Path to the input HDF5 file containing the data table.")
    #parser.add_argument('dataset_name', type=str, help ='Relative path to data_table (i.e., dataset name) in HDF5 file')
    #parser.add_argument('validity_thersholds_file', type=str, help="Path to the input YAML file containing calibration factors.")
    #parser.add_argument('output_file', type=str, help="Path to save the output calibrated data as a CSV file.")

    args = parser.parse_args()

    flag_type = args.flag_type
    data_file = args.data_file

    main(data_file, flag_type)