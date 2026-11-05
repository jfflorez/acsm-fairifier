
import os
from dash import html, dcc 
import dash_bootstrap_components as dbc
import dash_uploader as du 
from typing import Optional


def list_h5_files(server_folder: str) -> list:
    return sorted(f for f in os.listdir(server_folder) if f.endswith(('.h5', '.hdf5')))


def create_upload_component(server_folder: Optional[str] = None):
    """Build the file entry component of the layout.

    Args:
        server_folder (str, optional): Path to a folder that both JupyterLab and
            this app can read (shared folder), typically passed at layout
            definition time from an environment variable (e.g. APP_DATA_DIR).
            If given, the user picks an HDF5 file from that folder and nothing is
            uploaded. If None, the user uploads a file with dash-uploader.
    """
    if server_folder:
        entry = html.Div([
            dcc.Dropdown(
                id='file-picker',
                options=list_h5_files(server_folder),
                placeholder='Select an HDF5 file from the shared folder',
                style={'margin': '10px'},
            ),
            dbc.Button('Refresh list', id='refresh-files', size='sm', color='secondary'),
        ])
    else:
        entry = du.Upload(
            id='upload-image',
            text='Drag and Drop or Select Files',
            filetypes=['h5', 'hdf5'],  # optional: restrict to H5 files
            max_file_size=1024,        # MB limit (adjust as needed)
            default_style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px',
            },
        )

    # ----------------------------------------------------------------------
    # dcc.Upload is commented out on purpose: it encodes the whole file as
    # base64 and sends it inside the callback request, which adds significant
    # overhead (about 33% larger) to the browser-server payload. du.Upload
    # (dash-uploader) streams the file to the server in chunks instead.
    # ----------------------------------------------------------------------
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

    return dbc.Row(
        [html.H3("Open HDF5 file"), entry],
        justify="center", align="center",
        style={'background-color': '#f8f9fa', 'padding': '20px', 'text-align': 'center'},
    )