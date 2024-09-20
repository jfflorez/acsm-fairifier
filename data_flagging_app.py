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
# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

#df = pd.DataFrame.empty()

app.layout = dbc.Container([
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
                options=data_flagging_utils.dropdown_menu_options,
                )],
                width=12
        )],justify="center", align="center"),

    dbc.Row([
        dbc.Col([dbc.Button('Create Flag', id='flag-button', color="primary", className="mt-2")],width=2),
        dbc.Col([dbc.Button('Reset Flag', id='reset-flag-button', color="secondary", className="mt-2")],width=2),
        dbc.Col([dbc.Button('Commit Flag', id='commit-flag-button', color="secondary", className="mt-2")],width=2)
    ], justify="center", align="center"),
    
    dbc.Row([
        dbc.Col([ dcc.Graph(id='timeseries-plot')],  width=8), 
        #dbc.Col([html.Div(id='flag-record', style={'whiteSpace': 'pre-line'})], width=4), #config={'modeBarButtons': True,                                                         
                                                               #'modeBarButtonsToAdd':['select2d','lasso2d'], 
                                                               #'modeBarButtonsToRemove': ['zoom', 'pan']}),],  width=12)
        dbc.Col([dash_table.DataTable(data=[], 
                                      columns=[{"name": i, "id": i} for i in ['id','startdate','enddate','flag_description']], 
                                      id='tbl',
                                      style_header={'textAlign': 'center'},)], width=4)
        
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
            #content_type, content_string = contents.split(',')
            #decoded = base64.b64decode(content_string)
            #file_path = io.BytesIO(decoded)
            DataOps = hdf5_ops.HDF5DataOpsManager(path_to_file)
            df = DataOps.retrieve_dataframe_of_dataset_names()
            # TODO: allow selection of instrument folder
            instfolder = df['parent_instrument'].unique()[0]
            fig = data_flagging_utils.create_loaded_file_figure(path_to_file, instfolder)
            
            data['data_loaded_flag'] = True
            data['path_to_uploaded_file'] = path_to_file
            data['instfolder'] = instfolder
            
            return data, fig
        
        except Exception as e:
            print(f"Error processing file: {e}")
            return data, dash.no_update

    return data, dash.no_update

@app.callback(
    Output('timeseries-plot', 'figure', allow_duplicate=True),
    #Output('textarea-example-output','children'),
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
    value = '{} amigos'.format(n_clicks)
    #return fig, f'You have entered: \n{value}'
    return fig

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
     Output('timeseries-plot', 'figure', allow_duplicate=True)],
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
        return selected_data, fig
    else:
        return dash.no_update, dash.no_update

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
    instfolder = data['instfolder']
    flagfolderpath = os.path.join(os.path.splitext(data['path_to_uploaded_file'])[0],f'{instfolder}_flags')

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
        data = []
    else:
        data = []
        for pathtofile in dirlist_sorted_by_creation:
            if '.json' in pathtofile:
                with open(pathtofile,'r') as f:
                    data.append(json.load(f))

    number_of_existing_flags = len(dirlist_sorted_by_creation)
    flagid =  number_of_existing_flags+1
    flag_filename = os.path.join(flagfolderpath,f'flag_{flagid}.json')

    #if not os.path.exists(flag_filename):
    #    with open(flag_filename,'r') as open_flagsfile:
    #        json_flagsobject = json.load(open_flagsfile)   
    #        data = [json_flagsobject[key] for key in json_flagsobject.keys()]     


    #return f'You have entered: \n{value}'
    for key, value in selected_Data['range'].items():
        if 'x' in key:
            new_row = {'id':flagid,'startdate':value[0],'enddate':value[1],'flag_code': flag_value}
            new_row.update(data_flagging_utils.flags_dict[flag_value])
            data.append(new_row)
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

    return data
if __name__ == '__main__':
    app.run_server(debug=True)

