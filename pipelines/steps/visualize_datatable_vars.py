
import dima.src.hdf5_ops as dataOps
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def visualize_table_variables(data_file_path, dataset_name, flags_dataset_name, x_var, y_vars):



    if not os.path.exists(data_file_path): 
        raise ValueError(f"Path to input file {data_file_path} does not exists. The parameter 'data_file_path' must be a valid path to a suitable HDF5 file. ")
    
    # Create data manager object
    dataManager = dataOps.HDF5DataOpsManager(data_file_path)

    dataManager.load_file_obj()

    # Specify diagnostic variables and the associated flags 
    #dataset_name = 'ACSM_TOFWARE/2024/ACSM_JFJ_2024_meta.txt/data_table'
    #flags_dataset_name = 'ACSM_TOFWARE_flags/2024/ACSM_JFJ_2024_meta_flags.csv/data_table'
    dataset_df = dataManager.extract_dataset_as_dataframe(dataset_name)
    flags_df = dataManager.extract_dataset_as_dataframe(flags_dataset_name)

    if x_var not in dataset_df.columns and x_var not in flags_df.columns:
        raise ValueError(f'Invalid x_var : {x_var}. x_var must refer to a time variable name that is both in {dataset_name} and {flags_dataset_name}')

    flags_df[x_var] = pd.to_datetime(flags_df[x_var].apply(lambda x : x.decode(encoding="utf-8")))

    dataManager.unload_file_obj()

    if not all(var in dataset_df.columns for var in y_vars):
        raise ValueError(f'Invalid y_vars : {y_vars}. y_vars must be a subset of {dataset_df.columns}.')

    #fig, ax = plt.subplots(len(y_vars), 1, figsize=(12, 5))


    for var_idx, var in enumerate(y_vars):
        #y = dataset_df[var].to_numpy()
        
        # Plot Flow Rate
        fig = plt.figure(var_idx,figsize=(12, 2.5))
        ax = plt.gca()
        #ax = fig.get_axes()
        ax.plot(dataset_df[x_var], dataset_df[var], label=var, alpha=0.8, color='tab:blue')

        # Specify flag name associated with var name in y_vars. By construction, it is assumed the name satisfy the following sufix convention.
        var_flag_name = f"flag_{var}"        
        if var_flag_name in flags_df.columns:   
            # Identify valid and invalid indices         
            ind_valid = flags_df[var_flag_name].to_numpy()
            ind_invalid = np.logical_not(ind_valid)
            # Detect start and end indices of invalid regions
            # Find transition points in invalid regions
            invalid_starts = np.diff(np.concatenate(([False], ind_invalid, [False]))).nonzero()[0][::2]
            invalid_ends = np.diff(np.concatenate(([False], ind_invalid, [False]))).nonzero()[0][1::2]

            # Fill invalid regions                
            t_base = dataset_df[x_var].to_numpy()
            for start, end in zip(invalid_starts, invalid_ends):
                ax.fill_betweenx([dataset_df[var].min(), dataset_df[var].max()], t_base[start], t_base[end], 
                                    color='red', alpha=0.3, label="Invalid Data" if start == invalid_starts[0] else "")

        # Labels and Legends
        ax.set_xlabel(x_var)
        ax.set_ylabel(var)
        ax.legend()
        ax.grid(True)

                #plt.tight_layout()
                #plt.show()

    return fig, ax
    



