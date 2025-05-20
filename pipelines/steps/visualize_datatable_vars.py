
import dima.src.hdf5_ops as dataOps
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
def visualize_table_variables(data_file_path, dataset_name, flags_dataset_name, x_var, y_vars, yaxis_range_dict = {'FlowRate_ccs' : [0,100]}):



    if not os.path.exists(data_file_path): 
        raise ValueError(f"Path to input file {data_file_path} does not exists. The parameter 'data_file_path' must be a valid path to a suitable HDF5 file. ")
    APPEND_DIR = os.path.splitext(data_file_path)[0]
    if not os.path.exists(APPEND_DIR):
        APPEND_DIR = None

    # Create data manager object
    dataManager = dataOps.HDF5DataOpsManager(data_file_path)

    try:
        # Load the dataset
        dataManager.load_file_obj()
        dataset_df = dataManager.extract_dataset_as_dataframe(dataset_name)
    except Exception as e:
        print(f"Exception occurred while loading dataset: {e}")
    finally:
        # Unload file object to free resources
        dataManager.unload_file_obj()

    # Flags dataset loading and processing
    try:
        # Re-load the file for flags dataset
        dataManager.load_file_obj()
        flags_df = dataManager.extract_dataset_as_dataframe(flags_dataset_name)

        # Ensure the time variable exists in both datasets
        if x_var not in dataset_df.columns and x_var not in flags_df.columns:
            raise ValueError(f"Invalid x_var: {x_var}. x_var must exist in both {dataset_name} and {flags_dataset_name}.")

        # Convert the x_var column to datetime in flags_df
        flags_df[x_var] = pd.to_datetime(flags_df[x_var].apply(lambda x: x.decode(encoding="utf-8")))
    except Exception as e:
        dataManager.unload_file_obj()
        # If loading from the file fails, attempt alternative path
        if APPEND_DIR:
            # Remove 'data_table' part from the path for alternate location
            if 'data_table' in flags_dataset_name:
                flags_dataset_name_parts = flags_dataset_name.split(sep='/')
                flags_dataset_name_parts.remove('data_table')

            # Remove existing extension and append .csv
            base_path = os.path.join(APPEND_DIR, '/'.join(flags_dataset_name_parts))
            alternative_path = os.path.splitext(base_path)[0] + '_flags.csv'
        
            # Attempt to read CSV
            if not os.path.exists(alternative_path):
                raise FileNotFoundError(
                    f"File not found at {alternative_path}. Ensure there are flags associated with {data_file_path}."
                )
            flags_df = pd.read_csv(alternative_path)

            # Ensure the time variable exists in both datasets
            if x_var not in dataset_df.columns and x_var not in flags_df.columns:
                raise ValueError(f"Invalid x_var: {x_var}. x_var must exist in both {dataset_name} and {flags_dataset_name}.")

            # Apply datetime conversion on the x_var column in flags_df
            flags_df[x_var] = pd.to_datetime(flags_df[x_var].apply(lambda x: x))
    finally:
        # Ensure file object is unloaded after use
        dataManager.unload_file_obj()


    #if x_var not in dataset_df.columns and x_var not in flags_df.columns:
    #    raise ValueError(f'Invalid x_var : {x_var}. x_var must refer to a time variable name that is both in {dataset_name} and {flags_dataset_name}')

    #flags_df[x_var] = pd.to_datetime(flags_df[x_var].apply(lambda x : x.decode(encoding="utf-8")))

    #dataManager.unload_file_obj()

    if not all(var in dataset_df.columns for var in y_vars):
        raise ValueError(f'Invalid y_vars : {y_vars}. y_vars must be a subset of {dataset_df.columns}.')

    #fig, ax = plt.subplots(len(y_vars), 1, figsize=(12, 5))

    figs = []  # store each figure
    for var_idx, var in enumerate(y_vars):
        #y = dataset_df[var].to_numpy()
        
        # Plot Flow Rate
        #fig = plt.figure(var_idx,figsize=(12, 2.5))
        #ax = plt.gca()
        #ax.plot(dataset_df[x_var], dataset_df[var], label=var, alpha=0.8, color='tab:blue')

        fig = go.Figure()
        # Main line plot
        fig.add_trace(go.Scatter(
            x=dataset_df[x_var],
            y=dataset_df[var],
            mode='lines',
            name=var,
            line=dict(color='blue'),
            opacity=0.8
        ))
        

        # Specify flag name associated with var name in y_vars. By construction, it is assumed the name satisfy the following sufix convention.
        var_flag_name = f"flag_{var}"        
        if var_flag_name in flags_df.columns:   

            # Identify valid and invalid indices         
            ind_invalid = flags_df[var_flag_name].to_numpy()
            # ind_valid = np.logical_not(ind_valid) 
            # Detect start and end indices of invalid regions
            # Find transition points in invalid regions
            invalid_starts = np.diff(np.concatenate(([False], ind_invalid, [False]))).nonzero()[0][::2]
            invalid_ends = np.diff(np.concatenate(([False], ind_invalid, [False]))).nonzero()[0][1::2]

            # Fill invalid regions                
            t_base = dataset_df[x_var] #.to_numpy()
            
            y_min, y_max = dataset_df[var].min(), dataset_df[var].max()
            max_idx = len(t_base) - 1  # maximum valid index

            for start, end in zip(invalid_starts, invalid_ends):

                if start >= end:
                    print(f"Warning: Skipping invalid interval — start ({start}) >= end ({end})")
                    continue            # Clip start and end to valid index range
                start = max(0, start)
                end = min(end, max_idx)

                
                #ax.fill_betweenx([dataset_df[var].min(), dataset_df[var].max()], t_base[start], t_base[end], 
                #                    color='red', alpha=0.3, label="Invalid Data" if start == invalid_starts[0] else "")
                #                start = max(0, start)
                

                fig.add_shape(
                    type="rect",
                    x0=t_base[start], x1=t_base[end],
                    y0=y_min, y1=y_max,
                    fillcolor="red",
                    opacity=0.3,
                    line_width=0,
                    layer="below"
                )
            # Add a dummy invisible trace just for the legend
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(size=10, color='red', opacity=0.3),
                name='Invalid Region'
            ))

        # Labels and Legends
        #ax.set_xlabel(x_var)
        #ax.set_ylabel(var)
        #ax.legend()
        #ax.grid(True)

                #plt.tight_layout()
                #plt.show()

    #return fig, ax
        if var in yaxis_range_dict:
            y_axis_range = yaxis_range_dict[var]
        else:
            y_axis_range = [dataset_df[var].min(), dataset_df[var].max()]
        
        print('y axis range:',y_axis_range)
            
        # Add layout
        fig.update_layout(
                title=f"{var} over {x_var}",
                xaxis_title=x_var,
                yaxis_title=var,
                xaxis_range = [t_base.min(), t_base.max()],
                yaxis_range = y_axis_range,
                showlegend=True,
                height=300,
                margin=dict(l=40, r=20, t=40, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

        fig.show()
        figs.append(fig)

    # Optionally return figs if needed
    return figs
    

   