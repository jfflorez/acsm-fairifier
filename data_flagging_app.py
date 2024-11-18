import sys, os

import pandas as pd
import numpy as np

import base64
import dash
import io

# Set up project root directory
root_dir = os.path.abspath(os.curdir)
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir,'dima'))


import data_flagging_utils as data_flagging_utils

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

EnableVisCheckbox = dbc.Col(dbc.Row([dbc.Col(dcc.Checklist(
                                            id='enable-flag-checkbox',
                                            options=[{'label': html.Span('Enable Flag Visualization', style={'font-size': 15, 'padding-left': 10}), 'value': True}],
                                            value=[],
                                            inline=True),width=6),
                                    dbc.Col(dbc.Button("Load Flags", id='load-flags-button', color='primary'),width=4)],
                                    justify="center", align="center"),
                    width=12)

FlagVisTable =  html.Div(dash_table.DataTable(data=[], 
                                            columns=[{"name": i, "id": i} for i in ['id','startdate','enddate','flag_description','parent_ch_pos','parent_channel']], 
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

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

#df = pd.DataFrame.empty()

app.layout = dbc.Container([
    html.Div(children=[
                html.Div(children=[
                html.H1('QC/QA Data Flagging App'),
                html.H6('All measurements are assumed valid unless checked otherwise.')
                ]
            )],style={'textAlign': 'center'}),
    dbc.Row([ 

        dbc.Col([
                dcc.Upload(
                id='upload-image',
                children=html.Div(['Drag and Drop or ',html.A('Select Files')]),
                style={
                    'fontSize': "16px",
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                }),
                dcc.Dropdown(
                id='flag-options',
                options= data_flagging_utils.filter_flags_by_label(data_flagging_utils.flags_dict,'I'), # displays only flags to invalidate
                )],
                width=12
        ),
        #],justify="center", align="center"),

    #dbc.Row([
        dbc.Col([dbc.Button('Create Flag', id='flag-button', color="primary", className="mt-2")],width=2),
        dbc.Col([dbc.Button('Reset Flag', id='reset-flag-button', color="secondary", className="mt-2")],width=2),
        dbc.Col([dbc.Button('Commit Flag', id='commit-flag-button', color="secondary", className="mt-2")],width=2)
    ], justify="center", align="center",style={'background-color': '#f8f9fa', 'padding': '20px', 'text-align': 'center'}),
    
    dbc.Row([
        dbc.Col([ 
            html.Div([                
                    html.Div(id='flag-mode-title', style={'whiteSpace': 'pre-line'}),
                    dcc.Graph(id='timeseries-plot',
                              style={'height': '1200px','width' : '100%'})
                    ],
                    style={'height': '1000px', 'overflowY': 'auto'})        
        ],  
        width=8,
        style={'background-color': '#e9ecef', 'padding': '20px', 'text-align': 'center','height': '1000px'}), 
        #dbc.Col([html.Div(id='flag-record', style={'whiteSpace': 'pre-line'})], width=4), #config={'modeBarButtons': True,                                                         
                                                               #'modeBarButtonsToAdd':['select2d','lasso2d'], 
                                                               #'modeBarButtonsToRemove': ['zoom', 'pan']}),],  width=12)
        dbc.Col([
                html.Div([
                            EnableVisCheckbox,
                            FlagVisTable,                            
                            ReviewOpsPannel,
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

@app.callback(
    Output('memory-output','data'),
    Output('timeseries-plot', 'figure'),
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
            df = DataOps.dataset_metadata_df
            # TODO: allow selection of instrument folder
            instfolder = df['parent_instrument'].unique()[0]
            fig, channel_names = data_flagging_utils.create_loaded_file_figure(path_to_file, instfolder)
            
            data['data_loaded_flag'] = True
            data['path_to_uploaded_file'] = path_to_file
            data['instfolder'] = instfolder
            data['channel_names'] = channel_names

            DataOps.unload_file_obj()

            return data, fig
        
        except Exception as e:
            DataOps.unload_file_obj()
            print(f"Error processing file: {e}")
            return data, dash.no_update
        

    return data, dash.no_update

@app.callback(
    Output('timeseries-plot', 'figure', allow_duplicate=True),
    Output('flag-mode-title','children'),
    Input('flag-button', 'n_clicks'),
    State('timeseries-plot', 'figure'),
    State('memory-output', 'data'),
    prevent_initial_call=True
)
def create_flag(n_clicks, fig, data):
    if not data or not data.get('data_loaded_flag', False):
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
        instFolder =data['instfolder']
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
    instFolder = data['instfolder']
    filePath = data['path_to_uploaded_file']

    flagfolderpath = os.path.join(os.path.splitext(data['path_to_uploaded_file'])[0],f'{instFolder}_flags')

    if not os.path.isdir(flagfolderpath):
        os.makedirs(flagfolderpath)

    #dirlist = os.listdir(flagfolderpath)
    # Get all files in the directory with their full paths
    files = [os.path.join(flagfolderpath, f) for f in os.listdir(flagfolderpath)]

    # Sort files by creation time
    dirlist_sorted_by_creation = sorted(files, key=os.path.getctime)

    #dirlist = dirlist.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))

    display_flag_registry = True
    if not display_flag_registry:
        tableData = []
    else:
        tableData = data_flagging_utils.load_flags(filePath, instFolder)

        #tableData = []
        #for pathtofile in dirlist_sorted_by_creation:
        #    if '.json' in pathtofile:
        #        with open(pathtofile,'r') as f:
        #            tableData.append(json.load(f))

    number_of_existing_flags = len(dirlist_sorted_by_creation)
    flagid =  number_of_existing_flags+1
    flag_filename = os.path.join(flagfolderpath,f'flag_{flagid}.json')

    #if not os.path.exists(flag_filename):
    #    with open(flag_filename,'r') as open_flagsfile:
    #        json_flagsobject = json.load(open_flagsfile)   
    #        data = [json_flagsobject[key] for key in json_flagsobject.keys()]     


    #return f'You have entered: \n{value}'
    channel_names = data.get('channel_names', [])
    for key, value in selected_Data['range'].items():
        if 'x' in key:
            new_row = {'id':flagid,'startdate':value[0],'enddate':value[1],'flag_code': flag_value}
            new_row.update(data_flagging_utils.flags_dict.get(flag_value,{}))
            if channel_names:
                channel_pos =  extract_number(key)
                parent_channel, parent_dataset = tuple(channel_names[channel_pos].split(','))
                new_row.update({'parent_ch_pos': str(channel_pos), 'parent_channel':parent_channel, 'parent_dataset': parent_dataset})
            
            tableData.append(new_row)
            #data = [{'startdate':value[0],'enddate':value[1],'value':90}]

    
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

    
    instFolder = memoryData.get('instfolder', '')
    filePath = memoryData.get('path_to_uploaded_file', '')
    
    #flagfolderpath = os.path.join(os.path.splitext(memoryData['path_to_uploaded_file'])[0],f'{instfolder}_flags')

    if not filePath:
        return dash.no_update
    


       
    #flagfolderpath = os.path.join(os.path.splitext(memoryData['path_to_uploaded_file'])[0],f'{instfolder}_flags')
    ## Return no table update if there is no flags folder
    #if not os.path.exists(flagfolderpath):
    #    return dash.no_update
    
    #files = [os.path.join(flagfolderpath, f) for f in os.listdir(flagfolderpath)]

    vis_enabled = value[0] if value and isinstance(value, list) else False

    if n_clicks > 0 and vis_enabled: # and len(files) > 0:

        tableData = data_flagging_utils.load_flags(filePath, instFolder)

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
    """Wait for the server to start, then open the browser."""
    sleep(1)  # Wait briefly to ensure the server is starting
    webbrowser.open_new("http://127.0.0.1:8050/")

if __name__ == '__main__':
    # Start the browser-opening function in a separate thread
    threading.Thread(target=open_browser).start()
    
    # Run the Dash app server
    app.run_server(debug=True, use_reloader=False)