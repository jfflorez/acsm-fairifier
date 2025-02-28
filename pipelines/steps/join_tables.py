import argparse
import os
import pandas as pd
import json
import os
import pandas as pd

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

    
def get_metadata(path_to_file):

    path, filename = os.path.split(path_to_file)

    path_to_metadata = None
    for item in os.listdir(path):
        if 'metadata.json' in item:
            path_to_metadata = os.path.normpath(os.path.join(path,item))
    metadata = {}
    if path_to_file:
        with open(path_to_metadata,'r') as stream:
            metadata = json.load(stream)
    
        metadata = metadata.get(filename,{})

    return metadata

if __name__ == "__main__":
    
    path1 = 'data/collection_JFJ_2024_LeilaS_2025-02-17_2025-02-17/ACSM_TOFWARE_processed/2024/ACSM_JFJ_2024_timeseries_calibrated.csv'
    path2 = 'data/collection_JFJ_2024_LeilaS_2025-02-17_2025-02-17/ACSM_TOFWARE_processed/2024/ACSM_JFJ_2024_timeseries_calibration_factors.csv'
    path3 = 'data/collection_JFJ_2024_LeilaS_2025-02-17_2025-02-17/ACSM_TOFWARE_flags/2024/ACSM_JFJ_2024_timeseries_flags.csv'

    acum_df = join_tables([path1,path2])

    acum_df.to_csv('data/all_table.txt',sep='\t',index=None)

    acum_df = join_tables([path3])

    acum_df.to_csv('data/all_table_flags.txt',sep='\t',index=None)