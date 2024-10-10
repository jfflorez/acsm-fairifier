
import dima.src.hdf5_ops as h5de
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import base64
import os

import numpy as np
import pandas as pd
import dima.utils.g5505_utils as utils

UPLOAD_DIRECTORY = 'data_products/'

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

def save_file(name, content):
    # Decode the content and save the file
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    file_path = os.path.join(UPLOAD_DIRECTORY, name)
    with open(file_path, "wb") as f:
        f.write(decoded)
    return file_path

def create_loaded_file_figure(file_path, instfolder):

    DataOpsAPI = h5de.HDF5DataOpsManager(file_path)

    if not DataOpsAPI.file_obj:
        DataOpsAPI.load_file_obj()        

    target_channels = DataOpsAPI.file_obj[instfolder].attrs['target_channels']['names'][0].decode().split(',')
    target_loc = DataOpsAPI.file_obj[instfolder].attrs['target_channels']['location'][0].decode()
    diagnostic_channels = DataOpsAPI.file_obj[instfolder].attrs['diagnostic_channels']['names'][0].decode().split(',')
    diagnostic_loc = DataOpsAPI.file_obj[instfolder].attrs['diagnostic_channels']['location'][0].decode()

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
    
    DataOpsAPI.unload_file_obj()

    return fig

class FlaggingAppDataManager():

    def __init__(self, file_path, mode = 'r+') -> None:

        self.file_path = file_path
        self.mode = mode
        self._data_ops_obj = None
        self.file_obj = None
        self.datasets_metadata_df = None

        return None
    
    def load_file_obj(self):        
        self._data_ops_obj = h5de.HDF5DataOpsManager(self.file_path, self.mode)
        self._data_ops_obj.load_file_obj()
        self.file_obj = self._data_ops_obj.file_obj

    def unload_file_obj(self):        
        self._data_ops_obj = h5de.HDF5DataOpsManager(self.file_path, self.mode)
        self._data_ops_obj.unload_file_obj() # sets __data_ops_obj.file_obj to None  
   
    def transfer_flags(self):

        if self.file_obj is None:
            raise RuntimeError("File object is not loaded. Please load the HDF5 file using the 'load_file_obj' method before attempting to modify it.")

        path_to_append_dir, ext = os.path.splitext(self.file_path)
        self._data_ops_obj.update_file(path_to_append_dir)
        
    
    def apply_flags(self,instFolder):

        # TODO: apply flags to diagnostic and indivial channels. so far is all channels are cleaned

        if self.file_obj is None:
            raise RuntimeError("File object is not loaded. Please load the HDF5 file using the 'load_file_obj' method before attempting to modify it.")

        DataOpsManager = self._data_ops_obj
        file_obj = self.file_obj

        #with h5py.File(self.file_path, mode = self.mode, track_order=True) as file_obj:
        try:

            if not instFolder in file_obj:
                raise ValueError(f'Invalid instrument name. Instrument folder {instFolder} was not found in file {self.file_path}.')
            
            if not ('diagnostic_channels' in file_obj[instFolder].attrs and 'target_channels' in file_obj[instFolder].attrs):
                raise ValueError(
                    f'Required attributes missing. Instrument folder {instFolder} in file {self.file_path} has to be annotated with '
                    'attributes "diagnostic_channels" and "target_channels" that specify channels location and their names.'
                )           
            
            dataset_name = file_obj[instFolder].attrs['target_channels']['location'][0].decode()
            channel_names = file_obj[instFolder].attrs['target_channels']['names'][0].decode().split(',')

            dataset_obj = file_obj[dataset_name]
            # TODO: maybe we can do this directly on dataset = dataset_obj[...], which is a structured numpy array, instead of wrapping that as dataframe
            dataset_df = DataOpsManager.extract_dataset_as_dataframe(dataset_name)

            # Define datetime variable based on channel names. We assume by design the first entry of the list is the datetime variable name.
            datetime_var = channel_names[0]
            remaining_vars = channel_names.copy()
            remaining_vars.remove(datetime_var)

            ref_datetime_format = dataset_obj.attrs.get(datetime_var,None)['datetime_format'][0].decode()

            #datetime_var_data = pd.Series([item.decode() for item in dataset_obj[datetime_var]])
            #datetime_var_data = pd.to_datetime(datetime_var_data , format = ref_datetime_format, errors = 'coerce')
            dataset_df[datetime_var] = dataset_df[datetime_var].apply(lambda x: x.decode() )
            dataset_df[datetime_var] = pd.to_datetime(dataset_df[datetime_var], format = ref_datetime_format, errors = 'coerce')
            
            flag_indicator = np.zeros(shape = dataset_df[datetime_var].shape, 
                                      dtype = bool)

            # TODO: include this information as part of the flag's attributes in the flag recording process
            flag_datetime_format='%Y-%m-%d %H:%M:%S.%f'
            for flag in file_obj[f'{instFolder}_flags']:
                flag_obj = file_obj[f'{instFolder}_flags'][flag]['data_table']

                # Replace values indicated by flag NaN if flag label refers to invalidated data.
                if flag_obj['flag_label'][0].decode() == 'I':
                    t1 = pd.to_datetime(flag_obj['startdate'][0].decode(), format=flag_datetime_format)
                    t2 = pd.to_datetime(flag_obj['enddate'][0].decode(), format=flag_datetime_format)

                    t1_idx = abs(dataset_df[datetime_var]-t1).argmin()
                    t2_idx = abs(dataset_df[datetime_var]-t2).argmin()
                    
                    dataset_df.loc[t1_idx:t2_idx,remaining_vars] = np.nan


            # Apply the .strftime() method, handling NaT values by filling with an empty string or placeholder
            dataset_df[datetime_var] = dataset_df[datetime_var].apply(
                lambda x: x.strftime(ref_datetime_format).encode('utf-8') if not pd.isnull(x) else b''  # Handle NaT/NaN by returning empty string
            )


            #dt.strftime(ref_datetime_format).apply(lambda x: x.tobytes() if pd.notnull(x) else b'')

            dataset_name_parts = dataset_name.split('/')
            newInstFolder = '_'.join([dataset_name_parts[0],'cleaned'])
            dataset_name_parts.remove(dataset_name_parts[0])
            flagged_dataset_name = '/'.join(dataset_name_parts)


            dataset_dict = {'attributes':{},
                            'name':flagged_dataset_name,
                            'data': utils.convert_dataframe_to_np_structured_array(dataset_df)}
            
            dataset_dict['attributes'].update({'creation_date':utils.created_at().encode('utf-8')})
            dataset_dict['attributes'].update(dataset_obj.attrs)

                
            DataOpsManager.append_dataset(dataset_dict, newInstFolder)

        except Exception as e:
            self._data_ops_obj.unload_file_obj()
            print(f"An unexpected error occurred: {e}."
                   "The file object has been properly closed.")




                #flag_indicator[t1_idx:t2_idx] = True
                #(datetime_var_data-t1).min()

            #if not instrument_name in file_obj and not flag_name in file_obj:
            #    raise ValueError(f'Invalid instrument_name {instrument_name} and flag_name {flag_name}. No object with such names in file {self.file_path}')
            #if not f'{instrument_name}_flags':
            #    raise ValueError(f'There is no flags to work with. Make sure {instrument_name}_flags is created first before running this method.')

