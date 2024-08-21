
import dima.src.hdf5_data_extraction as h5de
from plotly.subplots import make_subplots
import plotly.graph_objs as go


flags_dict = {
        "000" : {"flag_label": 'V', "flag_description": "Valid measurement"},
        "100" : {"flag_label": 'V', "flag_description": "Checked by data originator. Valid measurement, overrides any invalid flags"},
        "110" : {"flag_label": 'V', "flag_description": "Episode data checked and accepted by data originator. Valid measurement"},
        "111" : {"flag_label": 'V', "flag_description": "Irregular data checked and accepted by data originator. Valid measurement"},
        "456" : {"flag_label": 'I', "flag_description": "Invalidated by data originator"},
        "460" : {"flag_label": 'I', "flag_description": "Contamination suspected"},
        "559" : {"flag_label": 'V', "flag_description": "Unspecified contamination or local influence, but considered valid"},
        "599" : {"flag_label": 'I', "flag_description": "Unspecified contamination or local influence"},
        "652" : {"flag_label": 'V', "flag_description": "construction/activity nearby"},
        "659" : {"flag_label": 'I', "flag_description": "Unspecified instrument/sampling anomaly"},
        "660" : {"flag_label": 'V', "flag_description": "Unspecified instrument/sampling anomaly"},
        "999" : {"flag_label": 'I', "flag_description": "Missing measurement, unspecified reason"}
        }

dropdown_menu_options = [{'label': flags_dict[key]['flag_description'], 'value': key} for key in flags_dict.keys()]

def create_loaded_file_figure(file_path):

    DataOpsAPI = h5de.HDF5DataOpsManager(file_path)        

    target_channels = DataOpsAPI.file_obj.attrs['target_channels']['names'][0].decode().split(',')
    target_loc = DataOpsAPI.file_obj.attrs['target_channels']['location'][0].decode()
    diagnostic_channels = DataOpsAPI.file_obj.attrs['diagnostic_channels']['names'][0].decode().split(',')
    diagnostic_loc = DataOpsAPI.file_obj.attrs['diagnostic_channels']['location'][0].decode()

    #fig = make_subplots(rows=(len(target_channels+diagnostic_channels)-2), cols=1, shared_xaxes=True,
    #                    row_heights = [1 for i in range(len(target_channels+diagnostic_channels)-2)])
    fig = make_subplots(rows=(len(target_channels+diagnostic_channels)-2), cols=1,
                        row_heights = [1 for i in range(len(target_channels+diagnostic_channels)-2)])
    traces = []
    trace_idx = 1
    dataset = DataOpsAPI.file_obj[target_loc]
    time_column = DataOpsAPI.reformat_datetime_column(target_loc,target_channels[0],'%d.%m.%Y %H:%M:%S.%f')
    
    
    for i in range(1,len(target_channels)):
        
        fig.add_trace(go.Scatter(x = time_column,
                                y = dataset[target_channels[i]][:],
                                mode = 'lines',
                                name = target_channels[i]), row=trace_idx, col=1)
        fig.update_yaxes(row=trace_idx, col=1)
        trace_idx = trace_idx + 1
        
    dataset = DataOpsAPI.file_obj[diagnostic_loc]
    time_column = DataOpsAPI.reformat_datetime_column(diagnostic_loc,diagnostic_channels[0],'%d.%m.%Y %H:%M:%S')
    for i in range(1,len(diagnostic_channels)):
        
        fig.add_trace(go.Scatter(x = time_column,
                                y = dataset[diagnostic_channels[i]][:],
                                mode = 'lines',
                                name = diagnostic_channels[i]), row=trace_idx, col=1)
        fig.update_yaxes(row=trace_idx, col=1, type="log")
        trace_idx = trace_idx + 1

    fig.update_layout(height=1200, title_text="Multiple Subplots with Shared Y-Axes")
    
    DataOpsAPI.close_file()

    return fig