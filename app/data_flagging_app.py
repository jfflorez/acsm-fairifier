import sys, os

try:
    thisFilePath = os.path.abspath(__file__)
    print(thisFilePath)
except NameError:
    print("[Notice] The __file__ attribute is unavailable in this environment (e.g., Jupyter or IDLE).")
    print("When using a terminal, make sure the working directory is set to the script's location to prevent path issues (for the DIMA submodule)")
    #print("Otherwise, path to submodule DIMA may not be resolved properly.")
    thisFilePath = os.getcwd()  # Use current directory or specify a default

projectPath = os.path.normpath(os.path.join(thisFilePath, "..",".."))

print(projectPath)

if not projectPath in sys.path:
    sys.path.insert(0,projectPath)

#print(dimaPath)
import pandas as pd
import numpy as np

import base64
import dash
import io

# Set up project root directory
#root_dir = os.path.abspath(os.curdir)
#sys.path.append(root_dir)
#sys.path.append(os.path.join(root_dir,'dima'))


import app.data_flagging_utils as data_flagging_utils
import dash_uploader as du
from dash import Patch, Dash, html, dcc, callback, Output, Input, State, dash_table
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
import json

import dima.src.hdf5_ops as hdf5_ops
#import dima.instruments.readers.filereader_registry as filereader_registry
#import instruments_.readers.flag_reader as flag_reader

#filereader_registry.file_extensions.append('.json') 
#filereader_registry.file_readers.update({'ACSM_TOFWARE_flags_json' : lambda x: flag_reader.read_jsonflag_as_dict(x)})

import threading
import webbrowser
from time import sleep


from app.components.instrument_dashboard import instrument_dashboard
from app.components.flagging_dashboard import flagging_dashboard
from app.components.upload_component import create_upload_component, list_h5_files #upload_component

import yaml
with open(os.path.join(projectPath,'app/flags/ebas_dict.yaml')) as stream:
    try:
        flags_dict = yaml.safe_load(stream)["flags"]
    except yaml.YAMLError as exc:
        flags_dict = {}
        print(exc)

EnableVisCheckbox = dbc.Col(dbc.Row([dbc.Col(dcc.Checklist(
                                            id='enable-flag-checkbox',
                                            options=[{'label': html.Span('Enable Flag Visualization', style={'font-size': 15, 'padding-left': 10}), 'value': True}],
                                            value=[],
                                            inline=True),width=6),
                                    dbc.Col(dbc.Button("Load Flags", id='load-flags-button', color='primary'),width=4)],
                                    justify="center", align="center"),
                    width=12)

FlagVisTable =  html.Div(dash_table.DataTable(id='tbl', 
                                            columns=[{"name": i, "id": i} for i in ['id','startdate','enddate','description','parent_channel']], 
                                            data=[],
                                            style_header={'textAlign': 'center'},
                                            fixed_rows={'headers': True},  # Fixed table headers
                                            style_table={'height': '1000px'},  # Make table scrollable
                                            style_cell={'textAlign': 'left', 'padding': '10px'},  # Cell styling
                                            ),
                        style={
                        'background-color': '#f0f0f0',  # Background color for the table
                        #'height': '1000px',  # Match the table's height
                        'padding': '5px',  # Optional padding around the table
                        'border': '1px solid #ccc',  # Optional border around the background
                         } )

ReviewOpsPannel =  dbc.Col([
                            # Row 1
                            dbc.Row([html.H2("Flagging workflow pannel", style={'font-size': 20})]),
                                

                            # Row 2
                            dbc.Row([
                                #dbc.Col(html.Div("Review Status"), width=6),
                                dcc.Checklist(
                                    id='flag-review-status-checklist',
                                    options=[
                                        {'label': [html.Span("Verify Flags", style={'font-size': 15, 'padding-left': 2})], 'value': 'will review'},
                                        {'label': [html.Span("Ready to Record Flags", style={'font-size': 15, 'padding-left': 2})], 'value': 'will transfer'},
                                        {'label': [html.Span("Finalize Flagging", style={'font-size': 15, 'padding-left': 2})], 'value': 'will apply'}
                                    ],
                                    value=[],
                                    #inline=True,
                                    style={
                                    "display": "flex",          # Flexbox for left alignment
                                    "flexDirection": "column",  # Arrange the items vertically
                                    "alignItems": "flex-start"  # Align the items to the left
    }
                                ),
                            ]),
                            
                            # Row 3
                            dbc.Row([
                                     #dbc.Col(dbc.Button("Load Flags", id='button-1', color='primary'),width=4),
                                     dbc.Col(dbc.Button("Delete Flag", id='delete-flag-button', color='primary'),width=4),
                                     dbc.Col(dbc.Button("Record Flags", id='button-2', color='primary'),width=4),
                                     dbc.Col(dbc.Button("Apply Flags", id='button-3', color='primary'),width=4)],
                                     justify="center", align="center"),
                            
                            # Row 4
                            #dbc.Row([
                            #    dbc.Col(html.Div("Apply Flags"), width=6),
                            #    dbc.Col(dbc.Button("Button 2", id='button-2', color='secondary'), width=6),
                            #]),
                            ],width=12)

DatePickerRange = dbc.Col([
    html.H2("Set date range for time series display", style={'font-size': '20px', 'margin-bottom': '10px'}),
    dcc.DatePickerRange(
        id='date-picker-range',
        display_format='YYYY-MM-DD',
        start_date_placeholder_text='Start Date',
        end_date_placeholder_text='End Date',
        minimum_nights=0,
        style={'width': '100%'}
    )
])

from dotenv import load_dotenv
load_dotenv(os.path.join(projectPath, '.env'))   # must run before any os.environ.get(...) is read

# Session base path on Renku (e.g. /sessions/<id>); empty locally
_BASE = os.environ.get("RENKU_BASE_URL_PATH", "").rstrip("/")
PREFIX = f"{_BASE}/dash-app/"

# Relative values resolve from projectPath; absolute values win (os.path.join drops projectPath).
DATA_DIR = os.path.join(projectPath, os.environ.get('APP_DATA_DIR', 'data'))
if not os.path.isdir(DATA_DIR):
    raise RuntimeError(f"APP_DATA_DIR does not exist: {DATA_DIR}")

SERVER_FOLDER = DATA_DIR if os.environ.get('APP_SHARED_MODE', '0') == '1' else None
UPLOAD_FOLDER_ROOT = DATA_DIR

#PREFIX = "/proxy/8050/"
# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    #routes_pathname_prefix= "/dash-app/", 
    routes_pathname_prefix = PREFIX if PREFIX != '/proxy/8050/' else '/', # Set to "/" if PREFIX='',
    requests_pathname_prefix=PREFIX,
)
du.configure_upload(
    app,
    UPLOAD_FOLDER_ROOT,
    use_upload_id=False,        
    upload_api=f"{PREFIX}dash-uploader"
    #upload_api="/dash-app/dash-uploader"
    #upload_api=f"{PREFIX}/API/dash-uploader",     # no prefix: the component adds it
)



print("Dash prefix:", app.config.requests_pathname_prefix)
print("Dash shared data folder:", SERVER_FOLDER)
#df = pd.DataFrame.empty()

app.layout = dbc.Container([
    html.Div(children=[
                html.Div(children=[
                html.H1('QC/QA Data Flagging App'),
                html.H6('All measurements are assumed valid unless checked otherwise.')
                ]
            )],style={'textAlign': 'center'}),
    create_upload_component(SERVER_FOLDER),
    instrument_dashboard,
    flagging_dashboard,
    
    dbc.Row([
        dbc.Col([ 
            html.Div([                
                    html.Div(id='flag-mode-title', style={'whiteSpace': 'pre-line'}),
                    dcc.Loading(
                    type="circle",  # Spinner style
                    delay_show=250,
                    children=[
                    dcc.Graph(id='timeseries-plot',
                              figure={},  # explicit empty figure, no initial render work
                              style={'height': '950px','width' : '100%'})]) # fits the 1000px container
                    ],
                    style={'height': '1000px', 'overflowY': 'auto'})        
        ],  
        width=8,
        style={'background-color': '#e9ecef', 'padding': '20px', 'text-align': 'center','height': '1000px'}), 
        #dbc.Col([html.Div(id='flag-record', style={'whiteSpace': 'pre-line'})], width=4), #config={'modeBarButtons': True,                                                         
                                                               #'modeBarButtonsToAdd':['select2d','lasso2d'], 
                                                               #'modeBarButtonsToRemove': ['zoom', 'pan']}),],  width=12)
        dbc.Col(
                [
                html.Div([
                            EnableVisCheckbox,
                            FlagVisTable,                            
                            DatePickerRange,
                        ], 
                        style={'height': '1000px','overflowY': 'auto'}),  # Set a fixed height for the div            
                ], 

                width=4,
                style={'background-color': '#dee2e6', 'padding': '20px', 'text-align': 'center','height': '1000px'},)
        
    ],justify="center", align="center"),

    dbc.Row([ # row 3
        dbc.Col([
            dcc.Store(id='memory-output'),            
            html.Div(id='textarea-example-output', style={'whiteSpace': 'pre-line'})
        ], width=12)
    ],justify="center", align="center"),
],  
)
# Supports file picker and data upload callbacks
def load_file(path_to_file : str):
    """Open the HDF5 file, read its metadata, and build what the UI needs.
    Shared by both modes. Returns (memory-output data, instrument options, disabled)."""
    data = {'data_loaded_flag': False}
    DataOps = None
    try:    
        DataOps = hdf5_ops.HDF5DataOpsManager(path_to_file)
        DataOps.load_file_obj()

        #content_type, content_string = contents.split(',')
        #decoded = base64.b64decode(content_string)
        #file_path = io.BytesIO(decoded)
        DataOps.extract_and_load_dataset_metadata()
        df = DataOps.dataset_metadata_df.copy()
        DataOps.unload_file_obj()

        # TODO: allow selection of instrument folder
        
        instrument_list = [{"label": instFolder, "value": instFolder} for instFolder in df['parent_instrument'].unique()]

        # Create list of file names in dict format for the first instFolder
        instFolderName = df['parent_instrument'].unique()[0]
        instFolderFileList = list(df.loc[df['parent_instrument']==instFolderName,'parent_file'].to_numpy())
        
        #file_list = [{"label": fileName, "value": fileName} for fileName in child_files]

        #fig, channel_names = data_flagging_utils.create_loaded_file_figure(path_to_file, instfolder)
        
        data['data_loaded_flag'] = True
        data['path_to_uploaded_file'] = path_to_file
        data['dataset_metadata_table'] = {}# df.to_dict()
        data[instFolderName] = instFolderFileList


        data['instFolder'] = instFolderName
        #data['channel_names'] = channel_names
        return data, instrument_list, False
    
    except Exception as e:
        print(f"Error processing file: {e}")
        return data, [], False
    finally:
        if DataOps is not None:
            DataOps.unload_file_obj()    

if SERVER_FOLDER:
    # ---- No data upload, assumes PROJECT_PATH/data folder hosts already the file on disk ----
    @app.callback(
        Output('memory-output', 'data', allow_duplicate=True),
        Output('instrument-dropdown', 'options'),
        Output('instrument-dropdown', 'disabled'),
        Input('file-picker', 'value'),
        prevent_initial_call=True,
    )
    def load_data_from_folder(name):
        if not name:
            return dash.no_update, dash.no_update, dash.no_update
        path_to_file = os.path.join(SERVER_FOLDER, os.path.basename(name))  # basename blocks '../'
        if not os.path.isfile(path_to_file):
            return dash.no_update, dash.no_update, dash.no_update
        return load_file(path_to_file)

    @app.callback(
        Output('file-picker', 'options'),
        Input('refresh-files', 'n_clicks'),
        prevent_initial_call=True,
    )
    def refresh_file_list(n_clicks):
        return list_h5_files(SERVER_FOLDER)

else:
    @app.callback(
        Output('memory-output','data', allow_duplicate=True),
        Output("instrument-dropdown", "options"),
        Output("instrument-dropdown", "disabled"),
        Input('upload-image', 'isCompleted'),
        State('upload-image', 'fileNames'),
        State('upload-image', 'upload_id'),
        #[Input('upload-image','filename'),
        #Input('upload-image','contents')],
        prevent_initial_call=True
    )
    def load_data(is_completed, filenames, upload_id):#(filename, contents):
        data = {'data_loaded_flag': False}
        if not is_completed:
            return data, [], False  # handle no upload case
        
        # Build the file path manually
        filename = filenames[0] if filenames else None
        if not filename:
            return {'data_loaded_flag': False}, [], False
        #path_to_file = os.path.join(DEFAULT_APP_DATA_DIR, upload_id, filename)
        path_to_file = os.path.join(UPLOAD_FOLDER_ROOT, filename)# upload_id, filename)

        return load_file(path_to_file)




@app.callback(
    Output("file-dropdown", "options"),
    Output("file-dropdown", "disabled"),
    Input("instrument-dropdown", "value"), 
    State('memory-output','data'),     
    prevent_initial_call=True
)
def update_file_dropdown(instFolderName, data):

    
    # Verify if dataset_metadata from uploaded HDF5 file was loaded correctly
    if not all([instFolderName, data]):
        return [], False
    
    if not 'dataset_metadata_table' in data.keys():
        return [], False
    

    file_list = []
    # Get files in instFolder
    instFolderFileList = data.get(instFolderName,[]) 

    # Otherwise, if there is no precomputed file list associated with a instFolder, compute that from dataset_metadata
    if instFolderFileList:        
        file_list = [{"label": fileName, "value": fileName} for fileName in instFolderFileList]
    else:
        path_to_file = data['path_to_uploaded_file']
        DataOps = hdf5_ops.HDF5DataOpsManager(path_to_file)
        DataOps.load_file_obj()

        #content_type, content_string = contents.split(',')
        #decoded = base64.b64decode(content_string)
        #file_path = io.BytesIO(decoded)
        DataOps.extract_and_load_dataset_metadata()
        tmp = DataOps.dataset_metadata_df.copy()
        DataOps.unload_file_obj()

        instFolderFileList = tmp.loc[tmp['parent_instrument']==instFolderName,'parent_file'].to_numpy()
        file_list = [{"label": fileName, "value": fileName} for fileName in instFolderFileList]

    return file_list, False

@app.callback(
    Output("sub-dropdown", "options"),
    Output("sub-dropdown", "disabled"),
    Output("sub-dropdown", "value"),
    Input("instrument-dropdown", "value"), 
    Input("file-dropdown", "value"), 
    State('memory-output','data'),     
    prevent_initial_call=True,
)
def update_variable_dropdown(instFolderName, fileName, data):

    
    # Verify if dataset_metadata from uploaded HDF5 file was loaded correctly
    #if not isinstance(data,dict):
    #    return [], False
    
    if not all([instFolderName, fileName, data]):
        return [], False, []
   

    #file_list = []
    # Get files in instFolder
    #instFolderFileList = data.get(instFolderName,[]) 

    # Otherwise, if there is no precomputed file list associated with a instFolder, compute that from dataset_metadata
    try:
        path_to_file = data['path_to_uploaded_file']
        DataOps = hdf5_ops.HDF5DataOpsManager(path_to_file)
        DataOps.load_file_obj()

        dataset_name = '/'.join([instFolderName,fileName,'data_table'])
        # Get attributes for data table 
        datetime_var, datetime_var_format = DataOps.infer_datetime_variable(dataset_name)
        metadata_dict = DataOps.get_metadata(dataset_name)

        #content_type, content_string = contents.split(',')
        #decoded = base64.b64decode(content_string)
        #file_path = io.BytesIO(decoded)
        #DataOps.extract_and_load_dataset_metadata()
        #tmp = DataOps.dataset_metadata_df.copy()
        #DataOps.unload_file_obj()

        

        #instFolderFileList = tmp.loc[tmp['parent_instrument']==instFolderName,'parent_file'].to_numpy()
        variableList = []
        for var_name in metadata_dict.keys():
            if var_name != datetime_var:
                variableList.append(var_name)

        DataOps.unload_file_obj()
    except Exception as e:
        DataOps.unload_file_obj()
        print(f"Error processing dataset_name: {e}")
        return [], False, [] 

    return [{"label": var_name, "value": var_name} for var_name in variableList] , False, variableList

from datetime import datetime


_TIME_CACHE = {}   # process-level cache: (path, mtime, dataset_name) -> datetime64[ns] array


@app.callback(
    Output('timeseries-plot', 'figure'),
    Output('memory-output', 'data'),
    Input('instrument-dropdown', 'value'),
    Input('file-dropdown', 'value'),
    Input('sub-dropdown', 'value'),
    # ======================================================================
    # TODO (possible improvement): move the date range out of this callback.
    # Replace these two Inputs with State, and add a separate `set_date_range`
    # callback that only patches the x-axis ranges, so a date change no longer
    # rebuilds and resends the whole figure.
    # ----------------------------------------------------------------------
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    # ======================================================================
    State('memory-output', 'data'),
    prevent_initial_call=True
)
def update_figure(instFolderName, fileName, variableList, start_date, end_date, data):

    fig = go.Figure()  # Always define it to avoid UnboundLocalError

    if not all([instFolderName, fileName, variableList, data]):
        return go.Figure(), dash.no_update

    path_to_file = data.get('path_to_uploaded_file')
    if not path_to_file:
        return go.Figure(), dash.no_update

    DataOps = None   # Avoids NameError in `finally` if the constructor fails
    try:
        DataOps = hdf5_ops.HDF5DataOpsManager(path_to_file)
        DataOps.load_file_obj()

        dataset_name = '/'.join([instFolderName, fileName, 'data_table'])

        # mtime in the key: a replaced/overwritten file never serves stale times.
        # datetime_var / format are no longer in the key, so on a cache hit
        # infer_datetime_variable is skipped entirely.
        cache_key = (path_to_file, os.path.getmtime(path_to_file), dataset_name)

        if cache_key in _TIME_CACHE:
            time_column = _TIME_CACHE[cache_key]   # already datetime64[ns]; treat as read-only
        else:
            datetime_var, datetime_var_format = DataOps.infer_datetime_variable(dataset_name)
            time_column = DataOps.reformat_datetime_column(
                dataset_name, datetime_var, datetime_var_format
            )
            # Convert once, on a miss, handling NaNs or invalid entries
            try:
                time_column = np.array(time_column, dtype='datetime64[ns]')
            except Exception:
                time_column = pd.to_datetime(time_column, errors='coerce').to_numpy()
            _TIME_CACHE[cache_key] = time_column

        # Exclude NaT values (creates a new array, so the cached one is not modified)
        mask = ~np.isnat(time_column)

        # ======================================================================
        # TODO (possible improvement): remove this date mask block.
        # With the date range handled by a separate `set_date_range` callback,
        # the figure would always be built with the full time range, and the
        # date picker would only move the x-axis ranges via Patch().
        # ----------------------------------------------------------------------
        if start_date and end_date:
            start = np.datetime64(start_date)
            end = np.datetime64(end_date)
            mask &= (time_column >= start) & (time_column <= end)
        # ======================================================================

        fig, channel_names = data_flagging_utils.create_loaded_file_figure(
            path_to_file, instFolderName, dataset_name, time_column, variableList, mask=mask
        )
        data['channel_names'] = channel_names

    except Exception as e:
        print(f'Error while processing file {path_to_file}: {e}')
    finally:
        if DataOps is not None:
            DataOps.unload_file_obj()

    # Drop any old browser-stored cache so it stops riding along in memory-output
    data.pop('time_cache', None)

    return fig, data



"""@app.callback(
    Output('memory-output','data'),
    Output('timeseries-plot', 'figure'),
    Output("instrument-dropdown", "options"),
    Output("instrument-dropdown", "disabled"),
    [Input('upload-image','filename')],
    [Input('upload-image','contents')]
)
def load_data(filename, contents):
    data = {'data_loaded_flag': False}
    if filename and contents and filename.endswith('.h5'):

        try:
            path_to_file = data_flagging_utils.save_file(filename,contents)

            DataOps = hdf5_ops.HDF5DataOpsManager(path_to_file)
            DataOps.load_file_obj()

            #content_type, content_string = contents.split(',')
            #decoded = base64.b64decode(content_string)
            #file_path = io.BytesIO(decoded)
            DataOps.extract_and_load_dataset_metadata()
            df = DataOps.dataset_metadata_df.copy()
            # TODO: allow selection of instrument folder
            instfolder = df['parent_instrument'].unique()[0]
            instrument_list = [{"label": instFolder, "value": instFolder} for instFolder in df['parent_instrument'].unique()]

            #fig, channel_names = data_flagging_utils.create_loaded_file_figure(path_to_file, instfolder)
            
            data['data_loaded_flag'] = True
            data['path_to_uploaded_file'] = path_to_file
            data['instfolder'] = instfolder
            #data['channel_names'] = channel_names

            DataOps.unload_file_obj()

            

            return data, dash.no_update, instrument_list, False
        
        except Exception as e:
            
            DataOps.unload_file_obj()
            print(f"Error processing file: {e}")
            return data, dash.no_update, instrument_list, False
        

    return data, dash.no_update, [], False"""

@app.callback(
    Output('timeseries-plot', 'figure', allow_duplicate=True),
    Output('flag-mode-title','children'),
    Input('flag-button', 'n_clicks'),
    #State('timeseries-plot', 'figure'), No need to pull the state to update the layout, we'll send a Patch applied on the front end side
    State('memory-output', 'data'),
    prevent_initial_call=True,
)
def create_flag(n_clicks, data):
    #if not data or not data.get('data_loaded_flag', False):

    if not all([n_clicks, data]):
        return dash.no_update, dash.no_update
    
    #fig['layout'].update({'dragmode' : 'select', 
    #                      'activeselection' : dict(fillcolor='yellow'),
    #                      'doubleClick' : 'reset'
    #                      })
    fig_patch = Patch()
    fig_patch['layout']['dragmode'] = 'select'
    fig_patch['layout']['activeselection'] = dict(fillcolor='yellow')

    title = "Flagging Mode Enabled: Select ROI to Define Flagging Interval."
    return fig_patch, title

#@app.callback(
#    Output('timeseries-plot', 'figure', allow_duplicate=True),
#    Output('timeseries-plot', 'selectedData', allow_duplicate=True),
#    #Output('textarea-example-output','children'),
#    Input('reset-flag-button', 'n_clicks'),
#    State('timeseries-plot', 'figure'),
#    #State('memory-output', 'data'),
#    prevent_initial_call=True
#)
#def clear_flag(n_clicks, fig):
    #if not data or not data.get('data_loaded_flag', False):
    #    return dash.no_update, dash.no_update
    
#    fig['layout'].update({'dragmode': 'zoom', 'activeselection': None})
    #fig.update_layout()
    #update_layout(dragmode='select', activeselection=dict(fillcolor='yellow'))
    
    #shapes = []
    #if relayoutData and 'xaxis.range[0]' in relayoutData:
    #    start = relayoutData['xaxis.range[0]']
    #    end = relayoutData['xaxis.range[1]']
    #else:
    #    start, end = None, None

    #if start and end:
    #    shapes.append({
    #        'type': 'rect',
    #        'xref': 'x',
    #        'yref': 'paper',
    #        'x0': start,
    #        'y0': 0,
    #        'x1': end,
    #        'y1': 1,
    #        'fillcolor': 'rgba(128, 0, 128, 0.3)',
    #        'line': {'width': 0}
    #    })
    #    fig['layout'].update(shapes=shapes)

    #value = '{} amigos'.format(n_clicks)
#    return fig, None #, f'You have entered: \n{value}'

@app.callback(
     Output('timeseries-plot', 'selectedData'),
     Output('timeseries-plot', 'figure', allow_duplicate=True),
     Output('flag-mode-title', 'children',allow_duplicate=True),     
     Input('reset-flag-button', 'n_clicks'),
     # State('timeseries-plot', 'figure'),
     State('memory-output', 'data'),
     prevent_initial_call = True)
def clear_flag(n_clicks, data):#(n_clicks, fig, data):    

    if not n_clicks or not data or not data.get('data_loaded_flag', False):
        return dash.no_update, dash.no_update, dash.no_update

    #if n_clicks > 0 and data.get('data_loaded_flag', False):       
        
    #fig['layout'].update({'dragmode': 'zoom', 'activeselection': None,
    #                      'selections':{'line': None}})
    #instFolder =data['instFolder']
    #fig['layout'].update({'title': f'{instFolder}: Target and Diagnostic Channels'})
    fig_patch = Patch()
    fig_patch['layout']['dragmode'] = 'zoom'
    fig_patch['layout']['activeselection'] = None
    fig_patch['layout']['selections'] = []
    fig_patch['layout']['title'] = f"{data['instFolder']}: Target and Diagnostic Channels"

    selected_data = None # Clear selection
    flagging_mode_message = '' # Clear title
    
    return selected_data, fig_patch, flagging_mode_message
    #else:
    #    return dash.no_update, dash.no_update, dash.no_update
    
@app.callback(
     Output('timeseries-plot', 'figure', allow_duplicate=True),
     Output('timeseries-plot', 'selectedData',allow_duplicate=True),
     Output('flag-mode-title', 'children',allow_duplicate=True),     
     Input('timeseries-plot', 'relayoutData'),
     # State('timeseries-plot', 'figure'), # increases payload unnecessarily in this case, instead we can get drag_mode from relayoutData
     State('memory-output', 'data'),
     prevent_initial_call = True)
def clear_flag_mode_title(relayoutData, data): # (relayoutData, fig, data): 
    if not relayoutData or not data or not data.get('data_loaded_flag', False):  
    #if not all([relayoutData, data]): # all([relayoutData, fig, data]):
        return dash.no_update, dash.no_update, dash.no_update

    mode = relayoutData.get('dragmode') # this is equivalent to mode = fig['layout'].get('dragmode',None)
    if mode in (None, 'select', 'lasso'):   # only act when the user picked another tool
        return dash.no_update, dash.no_update, dash.no_update
    #if data.get('data_loaded_flag', False) and not mode == 'select':


    #fig['layout'].update({'dragmode': 'zoom', 'activeselection': None,
    #                      'selections':{'line': None}})
    fig_patch = Patch()
    fig_patch['layout']['dragmode'] = 'zoom'
    fig_patch['layout']['activeselection'] = None
    fig_patch['layout']['selections'] = []

    #instFolder =data['instfolder']
    #fig['layout'].update({'title': f'{instFolder}: Target and Diagnostic Channels'})
    selected_data = None # Clear selection
    flagging_mode_message = '' # Clear title
    return fig_patch, selected_data, flagging_mode_message
    #else: # zoom/pan/etc., or still in flag mode
    #    return dash.no_update, dash.no_update, dash.no_update

def extract_number(s):
    return int(s[1:])-1 if s[1:].isdigit() else 0

@callback(Output('tbl', 'data'),
          Input('commit-flag-button','n_clicks'),
          State('flag-options','value'),
          State('timeseries-plot','selectedData'),
          State('memory-output', 'data'),
          prevent_initial_call=True)
def commit_flag(n_clicks,flag_value,selected_Data, data):

    value = selected_Data
    if (selected_Data is None) and (not isinstance(selected_Data,dict)):
        return []
    elif not selected_Data.get('range',[]): # verify if there is a flag's time interval to commit
        return []

    # TODO: modify the name path/to/name to reflect the directory provenance
    instFolder = data['instFolder']
    filePath = data['path_to_uploaded_file']

    # Modified version (appending "_flags" to the first folder)
    flagFolder = instFolder.split('/')
    flagFolder[0] = f"{flagFolder[0]}_flags"  # Modify first folder
    flagFolder = '/'.join(flagFolder)

    flagfolderpath = os.path.join(os.path.splitext(data['path_to_uploaded_file'])[0], flagFolder)
    flagfolderpath = os.path.normpath(flagfolderpath)

    #print("Without modification:", flagfolderpath_original)
    print("With modification:", flagfolderpath)

    if not os.path.isdir(flagfolderpath):
        os.makedirs(flagfolderpath)

    #dirlist = os.listdir(flagfolderpath)
    # Get all files in the directory with their full paths
    files = [os.path.join(flagfolderpath, f) for f in os.listdir(flagfolderpath)]

    # Sort files by creation time
    dirlist_sorted_by_creation = sorted(files, key=os.path.getctime)

    #dirlist = dirlist.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))

    display_flag_registry = True
    if display_flag_registry:
        tableData = data_flagging_utils.load_flags(flagfolderpath)
    else:
        tableData = []
        

        #tableData = []
        #for pathtofile in dirlist_sorted_by_creation:
        #    if '.json' in pathtofile:
        #        with open(pathtofile,'r') as f:
        #            tableData.append(json.load(f))

    number_of_existing_flags = len(dirlist_sorted_by_creation)
    flagid =  number_of_existing_flags+1
    

    #if not os.path.exists(flag_filename):
    #    with open(flag_filename,'r') as open_flagsfile:
    #        json_flagsobject = json.load(open_flagsfile)   
    #        data = [json_flagsobject[key] for key in json_flagsobject.keys()]     


    #return f'You have entered: \n{value}'
    channel_names = data.get('channel_names', [])
    for key, value in selected_Data['range'].items():
        if 'x' in key:
            new_row = {'id':flagid,'startdate':value[0],'enddate':value[1],'flag_code': flag_value}
            new_row.update(flags_dict.get(flag_value,{}))
            if channel_names:
                channel_pos =  extract_number(key)
                parent_channel, parent_dataset = tuple(channel_names[channel_pos].split(','))
                new_row.update({'parent_ch_pos': str(channel_pos), 'parent_channel':parent_channel, 'parent_dataset': parent_dataset})
            
            tableData.append(new_row)
            #data = [{'startdate':value[0],'enddate':value[1],'value':90}]

    flag_filename = os.path.join(flagfolderpath,f'flag_{flagid}_{parent_channel}.json')
    if not os.path.exists(flag_filename):
        with open(flag_filename,'w') as flagsfile:
            #json_flagsobject = json.dump({'row'+str(len(data)): new_row}, flagsfile)
            json.dump(new_row, flagsfile)
    #else:
    #    with open(flag_filename,'a') as flagsfile:
    #        json.dump(new_row, flagsfile)
            #json.dump({'row'+str(len(data)): new_row}, flagsfile)    
            #data = [json_flagsobject[key] for key in json_flagsobject.keys()] 

    return tableData

#@callback(Output('memory-output','data',allow_duplicate=True), 
#          [Input('enable-flag-checkbox', 'value'), State('memory-output','data')],
#          prevent_initial_call=True)
          #[Input('tbl','active_cell'), Input('enable-flag-checkbox', 'value') State('timeseries-plot', 'figure'), State('tbl','data')],)
#def enable_flag_visualization(value, memory):
#    if isinstance(memory,dict):
#        memory.update({'vis_enabled' : value})

#        return memory
    
#    return dash.no_update

@callback(Output('timeseries-plot', 'figure',allow_duplicate=True), 
          [Input('enable-flag-checkbox', 'value'), State('timeseries-plot', 'figure')],
          prevent_initial_call = True)
def clear_flags_from_figure(value, figure):

    vis_enabled = value[0] if value and isinstance(value, list) else False

    if not vis_enabled and figure:
        shapes = figure.get('layout', {}).get('shapes', [])
        
        if shapes:  # If there are shapes in the figure, clear them
            new_figure = figure.copy()  # Create a copy to avoid mutation
            new_figure['layout']['shapes'] = []
            return new_figure
    
    return dash.no_update


@callback(Output('timeseries-plot', 'figure',allow_duplicate=True), 
          [Input('tbl','active_cell'), 
           State('enable-flag-checkbox', 'value'), State('timeseries-plot', 'figure'), State('tbl','data')],
          prevent_initial_call = True)
def visualize_flag_on_figure(active_cell, value, figure, data):

    if value:
        vis_enabled = value[0]
    else:
        vis_enabled = False
    

    if active_cell and vis_enabled:
        row = active_cell['row']
        startdate = data[row]['startdate']
        enddate = data[row]['enddate']
        parent_ch_pos = data[row].get('parent_ch_pos',None)

        if parent_ch_pos != None:
            # Ensure that startdate and enddate are parsed correctly
            #startdate = pd.to_datetime(startdate)
            #enddate = pd.to_datetime(enddate)

            # Determine y-axis range directly from layout
            yaxis_key = f"yaxis{int(parent_ch_pos) + 1}" if int(parent_ch_pos) > 0 else "yaxis"
            xaxis_key = f"xaxis{int(parent_ch_pos) + 1}" if int(parent_ch_pos) > 0 else "xaxis"
            #y_min = figure['layout'].get(yaxis_key, {}).get('range', [0, 1])[0]
            #y_max = figure['layout'].get(yaxis_key, {}).get('range', [0, 1])[1]

            # Add a vertical region to the specified subplot
            xref=xaxis_key.replace('axis', ''),
            yref=yaxis_key.replace('axis', ''),
            figure['layout']['shapes'] = figure['layout'].get('shapes', []) + [
                dict(
                    type="rect",
                    xref=xref,
                    yref=yref,
                    x0=startdate,
                    x1=enddate,
                    y0=figure['layout'][yaxis_key]['range'][0],
                    y1=figure['layout'][yaxis_key]['range'][1],
                    line=dict(color="rgba(50, 171, 96, 1)", width=2),
                    fillcolor="rgba(50, 171, 96, 0.3)",
                )
            ]
        return figure
    
    return dash.no_update

@callback(Output('tbl', 'data',allow_duplicate=True),
          [Input('load-flags-button','n_clicks'),State('enable-flag-checkbox', 'value'),State('memory-output', 'data')],
          prevent_initial_call = True)
def visualize_flags_on_table(n_clicks,value,memoryData):

    
    instFolder = memoryData.get('instFolder', '')
    filePath = memoryData.get('path_to_uploaded_file', None)

   
    #flagfolderpath = os.path.join(os.path.splitext(memoryData['path_to_uploaded_file'])[0],f'{instfolder}_flags')

    if not filePath:
        return dash.no_update

    # Modified version (appending "_flags" to the first folder)
    flagFolder = instFolder.split('/')
    flagFolder[0] = f"{flagFolder[0]}_flags"  # Modify first folder
    flagFolder = '/'.join(flagFolder)

    # Remove .h5 ext from filepath and define expected flag folder
    flagfolderpath = os.path.join(os.path.splitext(filePath)[0], flagFolder)
    flagfolderpath = os.path.normpath(flagfolderpath)
    


       
    #flagfolderpath = os.path.join(os.path.splitext(memoryData['path_to_uploaded_file'])[0],f'{instfolder}_flags')
    ## Return no table update if there is no flags folder
    #if not os.path.exists(flagfolderpath):
    #    return dash.no_update
    
    #files = [os.path.join(flagfolderpath, f) for f in os.listdir(flagfolderpath)]

    vis_enabled = value[0] if value and isinstance(value, list) else False

    if n_clicks > 0 and vis_enabled: # and len(files) > 0:

        tableData = data_flagging_utils.load_flags(flagfolderpath)

        if not tableData:
            return dash.no_update    
        else:        
            return tableData
        
    #    # Sort files by creation time
    #    dirlist_sorted_by_creation = sorted(files, key=os.path.getctime)
    #    tableData = []
    #    for pathtofile in dirlist_sorted_by_creation:
    #        if '.json' in pathtofile:
    #            try:
    #                with open(pathtofile,'r') as f:
    #                    tableData.append(json.load(f))
    #            except (json.JSONDecodeError, FileNotFoundError) as e:
    #                print(e)
    #                continue  # Skip invalid or missing files

    #    return tableData
    
    return dash.no_update


def open_browser():
    """Wait for the server to start, then open the browser (only on the host)."""
    sleep(1)  # Give the server time to start

    # Open in browser only if running outside Docker
    if not os.getenv("DOCKER_CONTAINER"):  
        webbrowser.open_new("http://127.0.0.1:8050/")


def main():
    # Start the browser-opening function in a separate thread
    threading.Thread(target=open_browser).start()

    # Set DASH_DEBUG=0 for Renku deployment
    debug = os.environ.get("DASH_DEBUG", "1") == "1"   # default on = old behav
    # Run the Dash app server on 0.0.0.0 to allow external access
    app.run(host="0.0.0.0", port=8050, debug=debug, use_reloader=False)

if __name__ == '__main__':
    main()