
import dima.src.hdf5_ops as h5de
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import base64
import os

import numpy as np
import pandas as pd
import dima.utils.g5505_utils as utils

UPLOAD_DIRECTORY = 'data/'





def save_file(name, content):
    # Decode the content and save the file
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    file_path = os.path.join(UPLOAD_DIRECTORY, name)
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(decoded)
        print(f"File saved successfully at {file_path}")
        return file_path
    else:
        print(f'File already exists at {file_path}.\nTo maintain the integrity of the existing file, it will not be overwritten.')
        return file_path

def filter_flags_by_label(flags_dict, label):
    """
    Filters the flags dictionary by the specified label.
    If label is 'all', returns all flags without filtering.

    Parameters:
    -----------
        flags_dict (dict): The dictionary containing flags.
        label (str): The label to filter by ('I', 'V', or 'all').

    Returns:
    --------
        list: A list of dictionaries with 'label' and 'value' for the specified label,
              or all flags if label is 'all'.
    """
    return [
        {'label': value['description'], 'value': code}
        for code, value in flags_dict.items()
        if label == 'all' or value['validity'] == label
    ]

def create_loaded_file_figure(file_path, instFolder, dataset_name, time_column, variables, mask):

    DataOpsAPI = h5de.HDF5DataOpsManager(file_path)

    if not DataOpsAPI.file_obj:
        DataOpsAPI.load_file_obj()        

    #target_channels = DataOpsAPI.file_obj[instfolder].attrs['target_channels']['names'][0].decode().split(',')
    #target_loc = DataOpsAPI.file_obj[instfolder].attrs['target_channels']['location'][0].decode()
    #diagnostic_channels = DataOpsAPI.file_obj[instfolder].attrs['diagnostic_channels']['names'][0].decode().split(',')
    #diagnostic_loc = DataOpsAPI.file_obj[instfolder].attrs['diagnostic_channels']['location'][0].decode()

    #fig = make_subplots(rows=(len(target_channels+diagnostic_channels)-2), cols=1, shared_xaxes=True,
    #                    row_heights = [1 for i in range(len(target_channels+diagnostic_channels)-2)])
    fig = make_subplots(rows=(len(variables)), cols=1,
                        row_heights = [1 for i in range(len(variables))])
    traces = []
    trace_idx = 1

    indices = np.where(mask)[0]
    start_idx = indices[0]
    end_idx = indices[-1] + 1  # slice is exclusive end

    dataset = DataOpsAPI.file_obj[dataset_name]
    #time_column = DataOpsAPI.reformat_datetime_column(dataset_name,
    #                                                  datetime_var,
    #                                                  datetime_var_format)
    
    for i in range(0,len(variables)):

        x = time_column[start_idx:end_idx]
        y = dataset[variables[i]][start_idx:end_idx]
        
        fig.add_trace(go.Scatter(x = x,
                                y = y,
                                mode = 'lines',
                                name = variables[i]), row=trace_idx, col=1)
        fig.update_yaxes(title_text= variables[i], row=trace_idx, col=1)
        trace_idx = trace_idx + 1
        
    #dataset = DataOpsAPI.file_obj[diagnostic_loc]
    #time_column = DataOpsAPI.reformat_datetime_column(diagnostic_loc,diagnostic_channels[0],'%d.%m.%Y %H:%M:%S')
    #for i in range(1,len(diagnostic_channels)):
        
    #    fig.add_trace(go.Scatter(x = time_column,
    #                            y = dataset[diagnostic_channels[i]][:],
    #                            mode = 'lines',
    #                            name = diagnostic_channels[i]), row=trace_idx, col=1)
    #    fig.update_yaxes(title_text= diagnostic_channels[i], row=trace_idx, col=1, type="log")
    #    trace_idx = trace_idx + 1

    fig.update_layout(height=1200, title_text=f"{instFolder} : Target and Diagnostic Channels", showlegend=False)
    
    DataOpsAPI.unload_file_obj()
    #target_channels.remove(target_channels[0])
    #diagnostic_channels.remove(diagnostic_channels[0])
    return fig , [','.join([item,dataset_name]) for item in variables] #+ [','.join([item,diagnostic_loc]) for item in diagnostic_channels]

#import os
import json
import h5py

def load_flags(flagFolderPath, dry_run : bool = False): #filePath, instFolder, dry_run : bool = False):
    """
    Returns a list of flags (dictionaries) based on the provided filePath and instFolder.
    
    Parameters:
    -----------
        filePath (str): The path to the uploaded file, expected to have an .h5 extension.
        instFolder (str): The name of the instrument folder, which must exist as a group in the HDF5 file.
        dry_run (bool): If True, performs all operations except loading file contents.
    
    Returns:
    --------
        list: A list of dictionaries containing flag data (or file paths in dry_run mode), 
              or None if conditions are not met.
    """

    # Return None if the flags folder does not exist
    if not os.path.exists(flagFolderPath):
        return None

    # List files in the flags folder
    files = [os.path.join(flagFolderPath, f) for f in os.listdir(flagFolderPath)]

    # If no files found, return None
    if not files:
        return []

    # Sort files by creation time
    sortedFiles = sorted(files, key=os.path.getctime)

    if dry_run:
        print(f"Dry run: Found {len(sortedFiles)} files in the flags folder:")
        for filePath in sortedFiles:
            print(f" - {filePath}")
        return sortedFiles  # Return file paths in dry run mode

    # Process and load JSON files
    flagDataList = []
    for filePath in sortedFiles:
        if filePath.endswith('.json') and not filePath.endswith('metadata.json'):
            try:
                with open(filePath, 'r') as file:
                    flagDataList.append(json.load(file))
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error loading file {filePath}: {e}")
                continue  # Skip invalid or missing files

    return flagDataList

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
            
            if '_'.join([instFolder,'flags']) not in flag_obj:
                raise RuntimeWarning(f'There is no flags to apply. ')
            
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
                if not flag_obj['flag_code'][0].decode() is 'None':
                    flag_label = ''
                else:
                    flag_label = flag_obj['flag_label'][0].decode()

                if flag_label == 'I':
                    t1 = pd.to_datetime(flag_obj['startdate'][0].decode(), format=flag_datetime_format)
                    t2 = pd.to_datetime(flag_obj['enddate'][0].decode(), format=flag_datetime_format)

                    t1_idx = abs(dataset_df[datetime_var]-t1).argmin()
                    t2_idx = abs(dataset_df[datetime_var]-t2).argmin()
                    
                    dataset_df.loc[t1_idx:t2_idx,remaining_vars] = np.nan


            # Apply the .strftime() method, handling NaT values by filling with an empty string or placeholder
            dataset_df[datetime_var] = dataset_df[datetime_var].apply(
                lambda x: x.strftime(ref_datetime_format).encode('utf-8') if not pd.isnull(x) else b''  # Handle NaT/NaN by returning empty string
            )


            # Split full datasetname instFolder/fileName/datatable --> [instFolder, filename, datatable]
            dataset_name_parts = dataset_name.split('/')
            # Create new instFolder name to store dataset after applying flags
            newInstFolder = '_'.join([dataset_name_parts[0],'cleaned'])
            dataset_name_parts.remove(dataset_name_parts[0])
            # Put together relative datasetname. Note that instFolder is now missing.
            flagged_dataset_name = '/'.join(dataset_name_parts)

            dataset_dict = {'attributes':{},
                            'name':flagged_dataset_name,
                            'data': utils.convert_dataframe_to_np_structured_array(dataset_df)}
            
            dataset_dict['attributes'].update({'creation_date':utils.created_at().encode('utf-8')})
            dataset_dict['attributes'].update(dataset_obj.attrs)

                
            DataOpsManager.append_dataset(dataset_dict, newInstFolder)

        except Exception as e:
            self._data_ops_obj.unload_file_obj()
            print(f"An unexpected error occurred: {e}"
                   "The file object has been properly closed.")




                #flag_indicator[t1_idx:t2_idx] = True
                #(datetime_var_data-t1).min()

            #if not instrument_name in file_obj and not flag_name in file_obj:
            #    raise ValueError(f'Invalid instrument_name {instrument_name} and flag_name {flag_name}. No object with such names in file {self.file_path}')
            #if not f'{instrument_name}_flags':
            #    raise ValueError(f'There is no flags to work with. Make sure {instrument_name}_flags is created first before running this method.')

