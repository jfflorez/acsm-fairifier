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

import dima.src.hdf5_data_extraction as h5de
import dima.src.metadata_review_lib as ma
import dima.src.g5505_utils as utils


import data_flagging_utils as data_flagging_utils

from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

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
        dbc.Col([html.Div(id='flag-record', style={'whiteSpace': 'pre-line'})], width=4), #config={'modeBarButtons': True,                                                         
                                                               #'modeBarButtonsToAdd':['select2d','lasso2d'], 
                                                               #'modeBarButtonsToRemove': ['zoom', 'pan']}),],  width=12)
        
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
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            file_path = io.BytesIO(decoded)
            fig = data_flagging_utils.create_loaded_file_figure(file_path)
            
            data['data_loaded_flag'] = True
            
            return data, fig
        
        except Exception as e:
            print(f"Error processing file: {e}")
            return data, dash.no_update

    return data, dash.no_update

@app.callback(
    Output('timeseries-plot', 'figure', allow_duplicate=True),
    Output('textarea-example-output','children'),
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
    return fig, f'You have entered: \n{value}'

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

@callback(Output('flag-record', 'children'),
          Input('commit-flag-button','n_clicks'),
          State('timeseries-plot','selectedData'),
          prevent_initial_call=True)

def commit_flag(n_clicks,selected_Data):

    value = selected_Data
    return f'You have entered: \n{value}'
if __name__ == '__main__':
    app.run_server(debug=True)

