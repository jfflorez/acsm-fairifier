import os
import sys
import yaml
import argparse

try:
    thisFilePath = os.path.abspath(__file__)
    print(thisFilePath)
except NameError:
    print("[Notice] The __file__ attribute is unavailable in this environment (e.g., Jupyter or IDLE).")
    thisFilePath = os.getcwd()

projectPath = os.path.normpath(os.path.join(thisFilePath, "..", "..", '..'))

if projectPath not in sys.path:
    sys.path.insert(0, projectPath)

import dima.src.hdf5_ops as dataOps
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

def visualize_table_variables(data_file_path, dataset_name, flags_dataset_name, x_var, y_vars,
                              yaxis_range_dict={'FlowRate_ccs': [0, 100]},
                              capture_renku_metadata=False,
                              workflow_name="visualize_flagged_variables"):

    if not os.path.exists(data_file_path):
        raise ValueError(f"Path to input file {data_file_path} does not exists. The parameter 'data_file_path' must be a valid path to a suitable HDF5 file. ")

    APPEND_DIR = os.path.splitext(data_file_path)[0]
    if not os.path.exists(APPEND_DIR):
        APPEND_DIR = None

    # Create data manager object
    dataManager = dataOps.HDF5DataOpsManager(data_file_path)

    try:
        dataManager.load_file_obj()
        dataset_df = dataManager.extract_dataset_as_dataframe(dataset_name)
    except Exception as e:
        print(f"Exception occurred while loading dataset: {e}")
    finally:
        dataManager.unload_file_obj()

    try:
        dataManager.load_file_obj()
        flags_df = dataManager.extract_dataset_as_dataframe(flags_dataset_name)

        if x_var not in dataset_df.columns and x_var not in flags_df.columns:
            raise ValueError(f"Invalid x_var: {x_var}. x_var must exist in both {dataset_name} and {flags_dataset_name}.")

        flags_df[x_var] = pd.to_datetime(flags_df[x_var].apply(lambda x: x.decode(encoding="utf-8")))
    except Exception as e:
        dataManager.unload_file_obj()

        if APPEND_DIR:
            if 'data_table' in flags_dataset_name:
                flags_dataset_name_parts = flags_dataset_name.split(sep='/')
                flags_dataset_name_parts.remove('data_table')

            base_path = os.path.join(APPEND_DIR, '/'.join(flags_dataset_name_parts))
            alternative_path = os.path.splitext(base_path)[0] + '_flags.csv'

            if not os.path.exists(alternative_path):
                raise FileNotFoundError(
                    f"File not found at {alternative_path}. Ensure there are flags associated with {data_file_path}."
                )
            flags_df = pd.read_csv(alternative_path)

            if x_var not in dataset_df.columns and x_var not in flags_df.columns:
                raise ValueError(f"Invalid x_var: {x_var}. x_var must exist in both {dataset_name} and {flags_dataset_name}.")

            flags_df[x_var] = pd.to_datetime(flags_df[x_var].apply(lambda x: x))
    finally:
        dataManager.unload_file_obj()

    if not all(var in dataset_df.columns for var in y_vars):
        raise ValueError(f'Invalid y_vars : {y_vars}. y_vars must be a subset of {dataset_df.columns}.')

    figs = []
    output_paths = []
    figures_dir = os.path.join(projectPath, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    for var_idx, var in enumerate(y_vars):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dataset_df[x_var],
            y=dataset_df[var],
            mode='lines',
            name=var,
            line=dict(color='blue'),
            opacity=0.8
        ))

        var_flag_name = f"flag_{var}"
        if var_flag_name in flags_df.columns:
            ind_invalid = flags_df[var_flag_name].to_numpy()
            invalid_starts = np.diff(np.concatenate(([False], ind_invalid, [False]))).nonzero()[0][::2]
            invalid_ends = np.diff(np.concatenate(([False], ind_invalid, [False]))).nonzero()[0][1::2]
            t_base = dataset_df[x_var]

            y_min, y_max = dataset_df[var].min(), dataset_df[var].max()
            max_idx = len(t_base) - 1

            for start, end in zip(invalid_starts, invalid_ends):
                if start >= end:
                    print(f"Warning: Skipping invalid interval — start ({start}) >= end ({end})")
                    continue
                start = max(0, start)
                end = min(end, max_idx)

                fig.add_shape(
                    type="rect",
                    x0=t_base[start], x1=t_base[end],
                    y0=y_min, y1=y_max,
                    fillcolor="red",
                    opacity=0.3,
                    line_width=0,
                    layer="below"
                )

            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(size=10, color='red', opacity=0.3),
                name='Invalid Region'
            ))

        if var in yaxis_range_dict:
            y_axis_range = yaxis_range_dict[var]
        else:
            y_axis_range = [dataset_df[var].min(), dataset_df[var].max()]

        fig.update_layout(
            title=f"{var} over {x_var}",
            xaxis_title=x_var,
            yaxis_title=var,
            xaxis_range=[t_base.min(), t_base.max()],
            yaxis_range=y_axis_range,
            showlegend=True,
            height=300,
            margin=dict(l=40, r=20, t=40, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        fig_path = os.path.join(figures_dir, f"fig_{var_idx}_{var}.html")
        fig.write_html(fig_path)
        output_paths.append(fig_path)
        figs.append(fig)

        # Display figure in notebook
        fig.show()

    inputs = []
    outputs = []
    parameters = []

    if capture_renku_metadata:
        from workflows.utils import RenkuWorkflowBuilder

        inputs.append(("script_py", {'path': os.path.relpath(thisFilePath, start=projectPath)}))
        inputs.append(("data_file", {'path': os.path.relpath(data_file_path, start=projectPath)}))
        # Track alternative path if used
        if 'alternative_path' in locals():
            inputs.append(("alternative_flags_csv", {
                'path': os.path.relpath(alternative_path, start=projectPath),
                'implicit' : True
            }))

        for fig_path in output_paths:
            outputs.append((os.path.splitext(os.path.basename(fig_path))[0],
                            {'path': os.path.relpath(fig_path, start=projectPath)}))

        parameters.append(("dataset_name", {'value': dataset_name}))
        parameters.append(("flags_dataset_name", {'value': flags_dataset_name}))
        parameters.append(("x_var", {'value': x_var}))
        parameters.append(("y_vars", {'value': y_vars}))

        workflowfile_builder = RenkuWorkflowBuilder(name=workflow_name)
        workflowfile_builder.add_step(
            step_name=workflow_name,
            base_command="python",
            inputs=inputs,
            outputs=outputs,
            parameters=parameters
        )
        workflowfile_builder.save_to_file(os.path.join(projectPath, 'workflows'))

    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Visualize table variables and associated flags.")

    parser.add_argument("data_file_path", type=str, help="Path to HDF5 file")
    parser.add_argument("dataset_name", type=str, help="Dataset name in HDF5 file")
    parser.add_argument("flags_dataset_name", type=str, help="Flags dataset name")
    parser.add_argument("x_var", type=str, help="Time variable (x-axis)")
    parser.add_argument("y_vars", nargs='+', help="List of y-axis variable names")
    parser.add_argument("--capture_renku_metadata", action="store_true", help="Flag to capture Renku workflow metadata")

    args = parser.parse_args()

    visualize_table_variables(
        data_file_path=args.data_file_path,
        dataset_name=args.dataset_name,
        flags_dataset_name=args.flags_dataset_name,
        x_var=args.x_var,
        y_vars=args.y_vars,
        capture_renku_metadata=args.capture_renku_metadata
    )
