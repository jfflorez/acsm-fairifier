import sys
import os
import h5py
import numpy as np
import pandas as pd
# Set up project root directory
root_dir = os.path.abspath(os.curdir)
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir,'dima'))

import dima.src.hdf5_data_extraction as h5de
import dima.src.metadata_review_lib as ma
import dima.src.g5505_utils as utils
import base64
import dash
import io

import data_flagging_utils as data_flagging_utils

#import dash_core_components as dcc
#import dash_html_components as html
#from dash.dependencies import Input, Output, State

from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

import tempfile


app = dash.Dash(__name__)
app.layout = html.Div([
    html.Div([
            dcc.Upload(
            id='upload-image',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
                    ]), style={"fontSize": "16px",
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },)                
    ]),
    html.Div([
    dcc.Dropdown(
        id='flag-options',
        options=[{'label': data_flagging_utils.flags_dict[key]['flag_description'], 'value': key} for key in data_flagging_utils.flags_dict.keys()]#,
        #value='000'
    ),
    html.Button('Flag Selected', id='flag-button')
    ]),
    html.Div([
    dcc.Graph(id='timeseries-plot',
            config={
            'modeBarButtonsToAdd': ['select2d', 'lasso2d'],  # Add box select and lasso select tools
            'displaylogo': False  # Optionally remove the Plotly logo from the mode bar
            }),
    
    ]),
    dcc.Store(id='memory-output'),#, data=fig.to_dict()),  # Store the initial figure
    html.Div(id='textarea-example-output', style={'whiteSpace': 'pre-line'})
    #html.Div(id='output-container')
])

@app.callback(Output('memory-output','data'),
              Output('timeseries-plot', 'figure'),
                 [Input('upload-image','filename')],
                 [Input('upload-image','contents')]
)
def load_data(filename,contents):
    data = {'data_loaded_flag':False}
    if filename and contents and filename.endswith('.h5'):
        try:
            # Decode and read the uploaded file
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            file_path = io.BytesIO(decoded)
            
            # Create a temporary file to save the content
            #with tempfile.NamedTemporaryFile(delete=False, suffix='.h5') as temp_file:
            #    temp_file.write(decoded)
            #    temp_file_path = temp_file.name

            fig = data_flagging_utils.create_loaded_file_figure(file_path)
            
            # Return file path and other relevant info
            data['data_loaded_flag'] = True

            fig.update_layout(dragmode='select',
                  activeselection=dict(fillcolor='yellow'))
            return data, fig
        
        except Exception as e:
            print(f"Error processing file: {e}")
            return data, dash.no_update
        

    return data, dash.no_update
    

@app.callback(
    Output('timeseries-plot', 'figure',allow_duplicate=True),
    Output('textarea-example-output','children'),
    Input('timeseries-plot', 'relayoutData'),
    State('timeseries-plot', 'figure'),
    State('memory-output', 'data'),
    prevent_initial_call=True
)
def update_graph(relayoutData, fig, data):

    if data is None:
        return dash.no_update, dash.no_update    
        
    if data.get('data_loaded_flag',False) is False:
        return dash.no_update, dash.no_update 
    # If fig is None or in its initial state, return no_update
    #if fig is None or not fig['data']:  # Check if the figure is empty or in an initial state
    #    return dash.no_update, dash.no_update

    shapes = []
    
    # Handle case where relayoutData is provided
    if relayoutData and 'xaxis.range[0]' in relayoutData:
        start = relayoutData['xaxis.range[0]']
        end = relayoutData['xaxis.range[1]']
    else:
        start = None  # Set to default or previously known values
        end = None    # Set to default or previously known values

    if start and end:
        shapes.append({
            'type': 'rect',
            'xref': 'x',
            'yref': 'paper',
            'x0': start,
            'y0': 0,
            'x1': end,
            'y1': 1,
            'fillcolor': 'rgba(128, 0, 128, 0.3)',
            'line': {'width': 0}
        })
        
        # Update the figure with the new shape
        fig['layout'].update(shapes=shapes)
    
    value = 'hola amigos'
    #return fig, 'You have entered: \n{}'.format(value)
    return dash.no_update, 'You have entered: \n{}'.format(value)


#@app.callback(
    #Output('output-container', 'children'),
#    [Input('flag-button', 'n_clicks')],
#    [State('flag-options', 'value'),
#     State('timeseries-plot', 'relayoutData')]
#)
#def flag_data(n_clicks, flag, relayoutData):
#    if n_clicks and relayoutData and 'xaxis.range[0]' in relayoutData:
#        start = relayoutData['xaxis.range[0]']
#        end = relayoutData['xaxis.range[1]']
#        print(f'Flagged with: {flag} from {start} to {end}')
#    elif n_clicks:
#        print('Please select an interval to flag.')

#if __name__ == '__main__':
app.run_server(debug=True)

