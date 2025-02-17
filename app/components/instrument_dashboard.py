
from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import dash_bootstrap_components as dbc

instrument_dashboard = dbc.Row([
    html.H3("Select data table"),
        
    # First Dropdown (Instrument Folders)
    dcc.Dropdown(
        id="instrument-dropdown",
        options=[{"label": i, "value": i} for i in []],
        placeholder="Select an Instrument Folder",
    ),

    # Spinner wrapping the second and third dropdowns
    dcc.Loading(
        type="circle",  # Spinner style
        children=[
            # Second Dropdown (Files)
            dcc.Dropdown(
                id="file-dropdown",
                placeholder="Select a File",
                disabled=True  # Initially disabled
            ),
            
            # Third Dropdown (Sub-selection)
            dcc.Dropdown(
                id="sub-dropdown",
                placeholder="Select Variables",
                multi = True,
                disabled=True
            )
        ]
    )
    ], 
    justify="center", align="center",style={'background-color': '#f8f9fa', 'padding': '20px', 'text-align': 'center'})