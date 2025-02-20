from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import dash_bootstrap_components as dbc

import yaml


with open('app/flags/ebas_dict.yaml') as stream:
    try:
        flags_dict = yaml.safe_load(stream)["flags"]
    except yaml.YAMLError as exc:
        flags_dict = {}
        print(exc)

import data_flagging_utils

flagging_dashboard = dbc.Row([ 
    html.H3("Create flags"),

    #dbc.Row([
            dcc.Dropdown(
            id='flag-options',
            options= data_flagging_utils.filter_flags_by_label(flags_dict,'I'), # displays only flags to invalidate
           ),
           #],
            #width=12
    #),
        #],justify="center", align="center"),

    dbc.Row([
        dbc.Col([dbc.Button('Create Flag', id='flag-button', color="primary", className="mt-2")],width=2),
        dbc.Col([dbc.Button('Reset Flag', id='reset-flag-button', color="secondary", className="mt-2")],width=2),
        dbc.Col([dbc.Button('Commit Flag', id='commit-flag-button', color="secondary", className="mt-2")],width=2)
    ], justify="center", align="center",style={'background-color': '#f8f9fa', 'padding': '20px', 'text-align': 'center'})], 
    justify="center", align="center",style={'background-color': '#f8f9fa', 'padding': '20px', 'text-align': 'center'}
    )