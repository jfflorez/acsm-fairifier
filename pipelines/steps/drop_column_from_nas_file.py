import sys, os
import re

try:
    thisFilePath = os.path.abspath(__file__)
    print(thisFilePath)
except NameError:
    print("[Notice] The __file__ attribute is unavailable in this environment (e.g., Jupyter or IDLE).")
    print("When using a terminal, make sure the working directory is set to the script's location to prevent path issues (for the DIMA submodule)")
    #print("Otherwise, path to submodule DIMA may not be resolved properly.")
    thisFilePath = os.getcwd()  # Use current directory or specify a default


projectPath = os.path.normpath(os.path.join(thisFilePath, "..", "..",'..'))  # Move up to project root

if projectPath not in sys.path:
    sys.path.insert(0,projectPath)

import numpy as np
import pandas as pd
from dima.instruments.readers.nasa_ames_reader import read_nasa_ames_as_dict







def main(path_to_data_file, column_to_remove):

    if not path_to_data_file.endswith('.nas'):
        raise RuntimeError(f'Invalid file extension. The input file{path_to_data_file} must be a .nas file.')
    
    #path_to_data_file = os.path.join(projectPath,path_to_data_file)
    #path_to_data_file = os.path.normpath(path_to_data_file)
 #import pandas as pd

    idr_dict = read_nasa_ames_as_dict(path_to_data_file)
    header_metadata_dict = idr_dict['attributes_dict']

    # Locate the dataset
    dataset = None
    for d in idr_dict['datasets']:
        if d['name'] == 'data_table':
            dataset = d
            break

    if dataset is None:
        raise ValueError("Dataset named 'data_table' not found.")

    data_table = dataset['data']  # structured numpy array

    # Convert to DataFrame
    df = pd.DataFrame(data_table)

    # Drop the column
    index = data_table.dtype.names.index(column_to_remove)
    df = df.drop(columns=column_to_remove)

    # Update header part2
    part2 = header_metadata_dict['raw_header_part2']
    nvars = df.columns.size
    part2[1] = f'{nvars}\n'.encode('utf-8')

    part2_2_tmp = part2[2].decode('utf-8').strip().split()
    del part2_2_tmp[index]
    part2[2] = (' '.join(part2_2_tmp) + '\n').encode('utf-8')
    print(part2[2])

    del part2[4+index-1]

    part2_3_tmp = part2[3].decode('utf-8').strip().split()
    del part2_3_tmp[index]
    part2[3] = (' '.join(part2_3_tmp) + '\n').encode('utf-8')

    # Update header part1 (adjust header length)
    part1 = header_metadata_dict['raw_header_part1']
    part1_0_tmp = part1[0].decode('utf-8').split()
    header_length = int(part1_0_tmp[0]) - 1
    part1_0_tmp[0] = str(header_length)
    part1[0] = (' '.join(part1_0_tmp) + '\n').encode('utf-8')

    output_path = "output_file.na"  # or any .txt, .na, etc.

    

    

    # Read all lines once
    with open(path_to_data_file, 'rb') as file:
        raw_lines = file.readlines()

    data_table_lines = []
    for line_idx in range(len(raw_lines)):
        if line_idx >= header_metadata_dict['header_length']-1:
            line = raw_lines[line_idx]
            # Find all "fields" with positions (this preserves spacing info)
            fields = list(re.finditer(rb'\S+', line))
            if index < len(fields):
                # Remove the field at the given index by slicing the bytes
                start, end = fields[index].span()
                line = line[:start] + line[end:]  # Remove the selected field
            data_table_lines.append(line)






    # Extract header length from the first line
    #header_length = int(lines[0].split()[0])
    #file_header = lines[:header_length]

    # Split header in three parts, header preamble, var descriptions, and metadata pairs 
    #part1, part2, part3 = split_header(file_header)

    #var_descriptions = extract_var_descriptions(part2)

    #table_header = part3[len(part3)-1]

    processed_lines = header_metadata_dict['raw_header_part1']
    processed_lines = processed_lines + header_metadata_dict['raw_header_part2'] 
    processed_lines = processed_lines + header_metadata_dict['raw_header_part3'] 
    processed_lines = processed_lines + data_table_lines

    with open(path_to_data_file, 'wb') as f:
        # Write header part 1
        for line in processed_lines:
            f.write(line) 

if __name__ == '__main__':
    path_to_data_file = os.path.normpath(os.path.join(projectPath,'data/CH0001G.20240201010000.20250519140310.aerosol_mass_spectrometer.chemistry_ACSM.pm1_non_refractory.2mo.1h.CH02L_Aerodyne_ToF-ACSM_017.CH02L_Aerodyne_ToF-ACSM_JFJ.lev2.nas'))
    main(path_to_data_file, column_to_remove='inletP')