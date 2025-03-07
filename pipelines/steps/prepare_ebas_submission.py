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

    



if __name__ == "__main__":
    
    path1 = 'data/collection_JFJ_2024_LeilaS_2025-02-17_2025-02-17/ACSM_TOFWARE_processed/2024/ACSM_JFJ_2024_timeseries_calibrated.csv'
    path2 = 'data/collection_JFJ_2024_LeilaS_2025-02-17_2025-02-17/ACSM_TOFWARE_processed/2024/ACSM_JFJ_2024_timeseries_calibrated_err.csv'
    path3 = 'data/collection_JFJ_2024_LeilaS_2025-02-17_2025-02-17/ACSM_TOFWARE_processed/2024/ACSM_JFJ_2024_timeseries_calibration_factors.csv'
    path4 = 'data/collection_JFJ_2024_LeilaS_2025-02-17_2025-02-17/ACSM_TOFWARE_flags/2024/ACSM_JFJ_2024_timeseries_flags.csv'

    acum_df = join_tables([path1,path2,path3])

    acsm_to_ebas = load_project_yaml_files(projectPath, "acsm_to_ebas.yaml")

    # Select variables that are both in the acsm to ebas dict and acum_df
    reduced_set_of_vars = [key for key in acum_df.columns if key in acsm_to_ebas['renaming_map'].keys()]

    acum_df = acum_df.loc[:,reduced_set_of_vars].rename(columns=acsm_to_ebas['renaming_map'])
    #print("Before renaming:", acum_df.columns)
    #print("Renaming map keys:", acsm_to_ebas['renaming_map'].keys())

    
    

    #print(reduced_set_of_vars)
    
    flags_acum_df = join_tables([path4])
    flags_acum_df = flags_acum_df.rename(columns=acsm_to_ebas['renaming_map'])





    # Ensure time columns are datetime    
    acum_df['ACSM_time'] = pd.to_datetime(acum_df['ACSM_time'])
    flags_acum_df['ACSM_time'] = pd.to_datetime(acum_df['ACSM_time'])

    # Count the number of NaT (null) values
    num_nats = acum_df['ACSM_time'].isna().sum()
    # Get the total number of rows
    total_rows = len(acum_df)
    # Calculate the percentage of NaT values
    percentage_nats = (num_nats / total_rows) * 100

    print(f"Total rows: {total_rows}")
    print(f"NaT (missing) values: {num_nats}")
    print(f"Percentage of data loss: {percentage_nats:.2f}%")

    # Count the number of NaT (null) values
    num_nats = flags_acum_df['ACSM_time'].isna().sum()
    # Get the total number of rows
    total_rows = len(flags_acum_df)
    # Calculate the percentage of NaT values
    percentage_nats = (num_nats / total_rows) * 100
    print(f"Total rows: {total_rows}")
    print(f"NaT (missing) values: {num_nats}")
    print(f"Percentage of data loss: {percentage_nats:.2f}%")


    nat_acum = acum_df['ACSM_time'].isna()
    nat_flags = flags_acum_df['ACSM_time'].isna()

    valid_rows = ~(nat_acum | nat_flags)  # Compute valid rows in one step

    # Define file paths
    #path_to_detection_limits = os.path.normpath(os.path.join(projectPath, 'pipelines/params/limits_of_detection.yaml'))
    #path_to_station_params = os.path.normpath(os.path.join(projectPath, 'pipelines/params/station_params.yaml'))

    # Load YAML files
    #detection_limits = load_yaml(path_to_detection_limits)
    detection_limits = load_project_yaml_files(projectPath, "limits_of_detection.yaml")
    station_params = load_project_yaml_files(projectPath, "station_params.yaml") # load_yaml(path_to_station_params)

    # Extract dictionaries from required keys
    lod_dict = detection_limits.get('LOD', {}).get('variables',{})  # Extract "LOD" dictionary
    jfj_dict = station_params.get('stations', {}).get('JFJ', {})  # Extract "JFJ" dictionary

    # Convert dictionaries to DataFrames using the existing function
    lod_df = metadata_dict_to_dataframe(lod_dict, shape = (len(acum_df),len(lod_dict)))
    jfj_df = metadata_dict_to_dataframe(jfj_dict, shape = (len(acum_df),len(jfj_dict)))

    # Ensure indexes are properly aligned for merging
    acum_df = acum_df.reset_index()  # Convert index to a column for merging

    # Merge with LOD DataFrame
    acum_df = acum_df.merge(lod_df, left_index=True, right_index=True, how='left')

    # Merge with JFJ DataFrame
    acum_df = acum_df.merge(jfj_df, left_index=True, right_index=True, how='left')


    acum_df = acum_df.rename(columns=acsm_to_ebas['renaming_map'])

    
    #reduced_set_of_vars = [key for key in reduced_set_of_vars if '' not in key]
    acum_df.loc[valid_rows.to_numpy(),:].to_csv('data/JFJ_ACSM-017_2024.txt',sep='\t',index=None, date_format="%Y/%m/%d %H:%M:%S")
    flags_acum_df.loc[valid_rows.to_numpy(),:].to_csv('data/JFJ_ACSM-017_FLAGS_2024.txt',sep='\t',index=None, date_format="%Y/%m/%d %H:%M:%S")



    from third_party.acsmProcessingSoftware.src import rawto012

    app = rawto012.Application()
    infile = 'data/JFJ_ACSM-017_2024.txt'
    acq_err_log = 'data/JFJ_ACSM-017_FLAGS_2024.txt'
    outdir = 'data/'
    app.process(infile, acq_err_log, outdir=outdir)


