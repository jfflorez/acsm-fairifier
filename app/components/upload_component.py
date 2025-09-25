
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import dash_bootstrap_components as dbc
import dash_uploader as du 


upload_component = dbc.Row([
    html.H3("Open HDF5 file"),
    du.Upload(
        id='upload-image',  # same ID
        text='Drag and Drop or Select Files',  # same text
        filetypes=['h5', 'hdf5'],  # optional: restrict to H5 files
        max_file_size=1024,  # MB limit (adjust as needed)
        default_style={  # same styling
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        }
    ),    
    #dcc.Upload(
    #id='upload-image',
    #children=html.Div(['Drag and Drop or ',html.A('Select Files')]),
    #    style={
    #        'width': '100%',
    #        'height': '60px',
    #        'lineHeight': '60px',
    #        'borderWidth': '1px',
    #        'borderStyle': 'dashed',
    #        'borderRadius': '5px',
    #        'textAlign': 'center',
    #        'margin': '10px'
    #    }),
    ], 
    justify="center", align="center",style={'background-color': '#f8f9fa', 'padding': '20px', 'text-align': 'center'})