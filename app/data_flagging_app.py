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

from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
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
from app.components.upload_component import upload_component

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

FlagVisTable =  html.Div(dash_table.DataTable(data=[], 
                                            columns=[{"name": i, "id": i} for i in ['id','startdate','enddate','description','parent_channel']], 
                                            id='tbl',
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

import dash_uploader as du
#UPLOAD_FOLDER_ROOT = os.path.join(projectPath,'data','uploads')
UPLOAD_FOLDER_ROOT = os.path.join(projectPath,'data')
# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
du.configure_upload(app, UPLOAD_FOLDER_ROOT, use_upload_id=False)
#df = pd.DataFrame.empty()

app.layout = dbc.Container([
    html.Div(children=[
                html.Div(children=[
                html.H1('QC/QA Data Flagging App'),
                html.H6('All measurements are assumed valid unless checked otherwise.')
                ]
            )],style={'textAlign': 'center'}),
    upload_component,
    instrument_dashboard,
    flagging_dashboard,
    
    dbc.Row([
        dbc.Col([ 
            html.Div([                
                    html.Div(id='flag-mode-title', style={'whiteSpace': 'pre-line'}),
                    dcc.Loading(
                    type="circle",  # Spinner style
                    children=[
                    dcc.Graph(id='timeseries-plot',
                              style={'height': '1200px','width' : '100%'})])
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

#@app.callback()

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
    
    #if filename and contents and filename.endswith('.h5'):

    try:
        #path_to_file = data_flagging_utils.save_file(filename,contents)

        # Build the file path manually
        filename = filenames[0] if filenames else None
        #path_to_file = os.path.join(UPLOAD_FOLDER_ROOT, upload_id, filename)
        path_to_file = os.path.join(UPLOAD_FOLDER_ROOT, filename)# upload_id, filename)

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
        DataOps.unload_file_obj()
        

    return data, [], False

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
import numpy as np

@app.callback(    
    Output('timeseries-plot', 'figure'),
    Output('memory-output','data'),
    Input('instrument-dropdown', 'value'),
    Input('file-dropdown', 'value'),
    Input('sub-dropdown', 'value'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
    Input('memory-output', 'data'),
    prevent_initial_call=True
)
def update_figure(instFolderName, fileName, variableList, start_date, end_date, data):

    fig = go.Figure()  # Always define it to avoid UnboundLocalError

    if not all([instFolderName, fileName, variableList, data]):
        return go.Figure(), dash.no_update

    path_to_file = data.get('path_to_uploaded_file')
    if not path_to_file:
        return go.Figure(), dash.no_update

    try:
        DataOps = hdf5_ops.HDF5DataOpsManager(path_to_file)
        DataOps.load_file_obj()

        dataset_name = '/'.join([instFolderName, fileName, 'data_table'])
        datetime_var, datetime_var_format = DataOps.infer_datetime_variable(dataset_name)

        if not isinstance(data.get('time_cache'), dict):
            data['time_cache'] = {}

        cache_key = f"{path_to_file}|{dataset_name}|{datetime_var}|{datetime_var_format}"

        if cache_key in data['time_cache']:
            time_column = np.array(data['time_cache'][cache_key])
        else:
            time_column = DataOps.reformat_datetime_column(
                dataset_name, datetime_var, datetime_var_format
            )
            data['time_cache'][cache_key] = time_column.astype(str).tolist()

        # Convert to datetime64, safely handling NaNs or invalid entries
        try:
            time_column = np.array(time_column, dtype='datetime64[ns]')
        except Exception:
            # If conversion fails (e.g. mixed formats), fall back to pandas
            import pandas as pd
            time_column = pd.to_datetime(time_column, errors='coerce').to_numpy()

        # Apply mask if date range provided
        mask = ~np.isnat(time_column)  # Exclude NaT values

        if start_date and end_date:
            start = np.datetime64(start_date)
            end = np.datetime64(end_date)
            mask &= (time_column >= start) & (time_column <= end)


        fig, channel_names = data_flagging_utils.create_loaded_file_figure(
            path_to_file, instFolderName, dataset_name, time_column, variableList, mask=mask
        )
        data['channel_names'] = channel_names

    except Exception as e:
        print(f'Error while processing file {path_to_file}: {e}')
    finally:
        DataOps.unload_file_obj()

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
    State('timeseries-plot', 'figure'),
    State('memory-output', 'data'),
    prevent_initial_call=True,
)
def create_flag(n_clicks, fig, data):
    #if not data or not data.get('data_loaded_flag', False):

    if not all([n_clicks, fig, data]):
        return dash.no_update, dash.no_update
    
    fig['layout'].update({'dragmode' : 'select', 
                          'activeselection' : dict(fillcolor='yellow'),
                          'doubleClick' : 'reset'
                          })
    
    #fig['layout'].update({'title':"Flagging Mode Enabled: Select ROI to Define Flagging Interval."})

    #value = '{} amigos'.format(n_clicks)
    title = "Flagging Mode Enabled: Select ROI to Define Flagging Interval."
    return fig, title
    #return fig

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
    [Output('timeseries-plot', 'selectedData'),
     Output('timeseries-plot', 'figure', allow_duplicate=True),
     Output('flag-mode-title', 'children',allow_duplicate=True)],     
    [Input('reset-flag-button', 'n_clicks'),
     State('timeseries-plot', 'figure'),
     State('memory-output', 'data')],
     prevent_initial_call = True)
def clear_flag(n_clicks, fig, data):    

    if n_clicks > 0 and data.get('data_loaded_flag', False):
        # Clear selection
        selected_data = None
        fig['layout'].update({'dragmode': 'zoom', 'activeselection': None,
                              'selections':{'line': None}})
        instFolder =data['instFolder']
        fig['layout'].update({'title': f'{instFolder}: Target and Diagnostic Channels'})
        flagging_mode_message = ''
        return selected_data, fig, flagging_mode_message
    else:
        return dash.no_update, dash.no_update, dash.no_update
    
@app.callback(
    [Output('timeseries-plot', 'figure', allow_duplicate=True),
     Output('timeseries-plot', 'selectedData',allow_duplicate=True),
     Output('flag-mode-title', 'children',allow_duplicate=True)],     
    [Input('timeseries-plot', 'relayoutData'),
     State('timeseries-plot', 'figure'),
     State('memory-output', 'data')],
     prevent_initial_call = True)
def clear_flag_mode_title(relayoutData, fig, data):   
    if not all([relayoutData, fig, data]):
        return dash.no_update, dash.no_update, dash.no_update

    if data.get('data_loaded_flag', False) and not fig['layout'].get('dragmode',None) == 'select':
        # Clear selection
        selected_data = None
        fig['layout'].update({'dragmode': 'zoom', 'activeselection': None,
                              'selections':{'line': None}})
        #instFolder =data['instfolder']
        #fig['layout'].update({'title': f'{instFolder}: Target and Diagnostic Channels'})
        flagging_mode_message = ''
        return fig, selected_data, flagging_mode_message
    else:
        return dash.no_update, dash.no_update, dash.no_update

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
            figure['layout']['shapes'] = figure['layout'].get('shapes', []) + [
                dict(
                    type="rect",
                    xref=xaxis_key.replace('axis', ''),
                    yref=yaxis_key.replace('axis', ''),
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

    # Run the Dash app server on 0.0.0.0 to allow external access
    app.run(host="0.0.0.0", port=8050, debug=True, use_reloader=False)

if __name__ == '__main__':
    main()