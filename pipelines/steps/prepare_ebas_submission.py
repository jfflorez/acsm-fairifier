import sys, os

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

import argparse
import pandas as pd
import json, yaml
import numpy as np
from utils import get_metadata
from utils import metadata_dict_to_dataframe
from pipelines.steps.utils import load_project_yaml_files

def join_tables(csv_files: list):
    """
    Joins multiple CSV files based on their metadata-defined datetime column.

    Parameters
    ----------
    csv_files : list
        List of paths to CSV files.

    Returns
    -------
    pd.DataFrame
        Merged DataFrame.
    """
    if not all(isinstance(item, str) for item in csv_files):
        raise TypeError(f"Invalid parameter. csv_files contain non-str items: {[item for item in csv_files if not isinstance(item, str)]}")

    if not all(os.path.exists(item) and item.endswith('.csv') for item in csv_files):
        raise RuntimeError("Parameter csv_files contains either an unreachable/broken path or a non-CSV file.")

    acum_df = pd.read_csv(csv_files[0])
    left_datetime_var = get_metadata(csv_files[0]).get('datetime_var', None)    
    acum_df = acum_df.drop_duplicates(subset=[left_datetime_var])

    if left_datetime_var is None:
        raise ValueError(f"Missing datetime_var metadata in {csv_files[0]}")

    for idx in range(1, len(csv_files)):
        append_df = pd.read_csv(csv_files[idx])
        right_datetime_var = get_metadata(csv_files[idx]).get('datetime_var', None)

        if right_datetime_var is None:
            raise ValueError(f"Missing datetime_var metadata in {csv_files[idx]}")

        append_df = append_df.drop_duplicates(subset=[right_datetime_var])
        acum_df = acum_df.merge(append_df, left_on=left_datetime_var, right_on=right_datetime_var, how='left')

    return acum_df

#import argparse
#import os
#import pandas as pd
from third_party.acsmProcessingSoftware.src import rawto012
#from utils import load_project_yaml_files, metadata_dict_to_dataframe, join_tables  # Adjust imports based on actual file locations

def main(paths_to_processed_files : list, path_to_flags : str, month : int = None):
    # Set up argument parsing

    acum_df = join_tables(paths_to_processed_files)
    acsm_to_ebas = load_project_yaml_files(projectPath, "acsm_to_ebas.yaml")

    # Select variables that are both in the acsm_to_ebas dict and acum_df
    reduced_set_of_vars = [key for key in acum_df.columns if key in acsm_to_ebas['renaming_map'].keys()]
    acum_df = acum_df.loc[:, reduced_set_of_vars].rename(columns=acsm_to_ebas['renaming_map'])

    flags_acum_df = join_tables([path_to_flags])
    flags_acum_df = flags_acum_df.rename(columns=acsm_to_ebas['renaming_map'])

    # Ensure time columns are datetime    
    acum_df['ACSM_time'] = pd.to_datetime(acum_df['ACSM_time'])
    flags_acum_df['ACSM_time'] = pd.to_datetime(flags_acum_df['ACSM_time'])

    # Apply month filter if specified
    if month:
        acum_df = acum_df[acum_df['ACSM_time'].dt.month == month]
        flags_acum_df = flags_acum_df[flags_acum_df['ACSM_time'].dt.month == month]

    # Count the number of NaT (null) values
    num_nats = acum_df['ACSM_time'].isna().sum()
    total_rows = len(acum_df)
    percentage_nats = (num_nats / total_rows) * 100

    print(f"Total rows: {total_rows}")
    print(f"NaT (missing) values: {num_nats}")
    print(f"Percentage of data loss: {percentage_nats:.2f}%")

    num_nats = flags_acum_df['ACSM_time'].isna().sum()
    total_rows = len(flags_acum_df)
    percentage_nats = (num_nats / total_rows) * 100

    print(f"Total rows: {total_rows}")
    print(f"NaT (missing) values: {num_nats}")
    print(f"Percentage of data loss: {percentage_nats:.2f}%")

    nat_acum = acum_df['ACSM_time'].isna()
    nat_flags = flags_acum_df['ACSM_time'].isna()

    valid_rows = ~(nat_acum | nat_flags)  # Compute valid rows in one step

    # Load YAML files
    detection_limits = load_project_yaml_files(projectPath, "limits_of_detection.yaml")
    station_params = load_project_yaml_files(projectPath, "station_params.yaml")

    # Extract dictionaries from required keys
    lod_dict = detection_limits.get('LOD', {}).get('variables', {})
    jfj_dict = station_params.get('stations', {}).get('JFJ', {})

    # Convert dictionaries to DataFrames using the existing function
    lod_df = metadata_dict_to_dataframe(lod_dict, shape=(len(acum_df), len(lod_dict)))
    jfj_df = metadata_dict_to_dataframe(jfj_dict, shape=(len(acum_df), len(jfj_dict)))

    # Ensure indexes are properly aligned for merging
    acum_df = acum_df.reset_index()  # Convert index to a column for merging

    # Merge with LOD DataFrame
    acum_df = acum_df.merge(lod_df, left_index=True, right_index=True, how='left')

    # Merge with JFJ DataFrame
    acum_df = acum_df.merge(jfj_df, left_index=True, right_index=True, how='left')

    acum_df = acum_df.rename(columns=acsm_to_ebas['renaming_map'])

    # Save results
    output_dir = os.path.join(projectPath,'data')
    output_file1 = os.path.join(output_dir, 'JFJ_ACSM-017_2024.txt')
    output_file2 = os.path.join(output_dir, 'JFJ_ACSM-017_FLAGS_2024.txt')
    #output_file1 = os.path.join(output_dir, f'JFJ_ACSM-017_2024_month{args.month}.txt' if args.month else 'JFJ_ACSM-017_2024.txt')
    #output_file2 = os.path.join(output_dir, f'JFJ_ACSM-017_FLAGS_2024_month{args.month}.txt' if args.month else 'JFJ_ACSM-017_FLAGS_2024.txt')

    acum_df.loc[:, :].to_csv(output_file1, sep='\t', index=None, date_format="%Y/%m/%d %H:%M:%S")
    flags_acum_df.loc[:, :].to_csv(output_file2, sep='\t', index=None, date_format="%Y/%m/%d %H:%M:%S")

    # Run external processing application
    app = rawto012.Application()
    infile = output_file1
    acq_err_log = output_file2
    outdir = output_dir
    app.process(infile, acq_err_log, outdir=outdir)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Process and calibrate ACSM data for JFJ station.")    
    parser.add_argument('--acsm_paths', type=str, required=True, nargs=3, help="Paths to the ACSM timeseries calibrated CSV file, the error CSV file, and the calibration factors CSV file.")
    parser.add_argument('--acsm_flags_path', type=str, required=True, help="Path to the ACSM flags CSV file.")
    parser.add_argument('--month', type=int, choices=range(1, 13), help="Filter data for a specific month (1-12).")

    args = parser.parse_args()

    # Load data
    csv_files = args.acsm_paths # list of filenames 
    flags_file = args.acsm_flags_path
    month = args.month
    main(csv_files, flags_file, month)
