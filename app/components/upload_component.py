
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import dash_bootstrap_components as dbc

upload_component = dbc.Row([
    html.H3("Open HDF5 file"),

    
    dcc.Upload(
    id='upload-image',
    children=html.Div(['Drag and Drop or ',html.A('Select Files')]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        }),
    ], 
    justify="center", align="center",style={'background-color': '#f8f9fa', 'padding': '20px', 'text-align': 'center'})