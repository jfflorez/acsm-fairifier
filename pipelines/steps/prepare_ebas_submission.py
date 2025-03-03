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

import argparse
import pandas as pd
import json, yaml
import pandas as pd
from utils import get_metadata

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

    if left_datetime_var is None:
        raise ValueError(f"Missing datetime_var metadata in {csv_files[0]}")

    for idx in range(1, len(csv_files)):
        append_df = pd.read_csv(csv_files[idx])
        right_datetime_var = get_metadata(csv_files[idx]).get('datetime_var', None)

        if right_datetime_var is None:
            raise ValueError(f"Missing datetime_var metadata in {csv_files[idx]}")

        acum_df = acum_df.merge(append_df, left_on=left_datetime_var, right_on=right_datetime_var, how='inner')

    return acum_df

    
def load_acsm_to_ebas_dict():

    # Implicit input
    dict_file = os.path.normpath(os.path.join(projectPath,"pipelines/dictionaries/acsm_to_ebas.yaml"))

    output_dict = {}
    try:
        with open(dict_file, 'r') as stream:
            output_dict = yaml.load(stream, Loader=yaml.FullLoader)
    except Exception as e:
        
        print(f'Error loading {dict_file}: {e}')
        return {}
    
    return output_dict
    

if __name__ == "__main__":
    
    path1 = 'data/collection_JFJ_2024_LeilaS_2025-02-17_2025-02-17/ACSM_TOFWARE_processed/2024/ACSM_JFJ_2024_timeseries_calibrated.csv'
    path2 = 'data/collection_JFJ_2024_LeilaS_2025-02-17_2025-02-17/ACSM_TOFWARE_processed/2024/ACSM_JFJ_2024_timeseries_calibration_factors.csv'
    path3 = 'data/collection_JFJ_2024_LeilaS_2025-02-17_2025-02-17/ACSM_TOFWARE_flags/2024/ACSM_JFJ_2024_timeseries_flags.csv'

    acum_df = join_tables([path1,path2])

    acsm_to_ebas = load_acsm_to_ebas_dict()    

    #print("Before renaming:", acum_df.columns)
    #print("Renaming map keys:", acsm_to_ebas['renaming_map'].keys())

    acum_df = acum_df.rename(columns=acsm_to_ebas['renaming_map'])
    acum_df['ACSM_time'] = pd.to_datetime(acum_df['ACSM_time'])

    reduced_set_of_vars = [key for key in acum_df.columns if 'factor' not in key]
    print(reduced_set_of_vars)
    acum_df.loc[:,reduced_set_of_vars].to_csv('data/JFJ_ACSM-017_2024.txt',sep='\t',index=None, date_format="%Y/%m/%d %H:%M:%S")

    # Count the number of NaT (null) values
    num_nats = acum_df['ACSM_time'].isna().sum()

    # Get the total number of rows
    total_rows = len(acum_df)

    # Calculate the percentage of NaT values
    percentage_nats = (num_nats / total_rows) * 100

    print(f"Total rows: {total_rows}")
    print(f"NaT (missing) values: {num_nats}")
    print(f"Percentage of data loss: {percentage_nats:.2f}%")

    acum_df = join_tables([path3])
    acum_df = acum_df.rename(columns=acsm_to_ebas['renaming_map'])
    acum_df['ACSM_time'] = pd.to_datetime(acum_df['ACSM_time'])


    # Count the number of NaT (null) values
    num_nats = acum_df['ACSM_time'].isna().sum()

    # Get the total number of rows
    total_rows = len(acum_df)

    # Calculate the percentage of NaT values
    percentage_nats = (num_nats / total_rows) * 100

    print(f"Total rows: {total_rows}")
    print(f"NaT (missing) values: {num_nats}")
    print(f"Percentage of data loss: {percentage_nats:.2f}%")

    acum_df.to_csv('data/JFJ_ACSM-017_FLAGS_2024.txt',sep='\t',index=None, date_format="%Y/%m/%d %H:%M:%S")