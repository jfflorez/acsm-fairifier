#!/bin/bash

# Define the name and location of the environment
ENV_NAME="multiphase_chem_env"
ENV_PATH="./envs/$ENV_NAME"  # Define a custom output folder

# Check if mamba is available and use it instead of conda for faster installation
if command -v mamba &> /dev/null; then
    CONDA_COMMAND="mamba"
else
    CONDA_COMMAND="conda"
fi

# Create the conda environment with all dependencies
$CONDA_COMMAND create -y -p "$ENV_PATH" python=3.11 \
    jupyter numpy pandas matplotlib plotly=5.24 scipy pip

# Activate the new environment
source activate "$ENV_PATH" || conda activate "$ENV_PATH"

# Install pip packages in one go to avoid repeated initializations
pip install h5py==3.10 pybis==1.35 igor2 ipykernel dash dash-bootstrap-components

# Export the environment to a YAML file
$CONDA_COMMAND env export --prefix "$ENV_PATH" > "$ENV_PATH/environment.yaml"

# Print success message
echo "Environment '$ENV_NAME' created successfully at '$ENV_PATH'."
echo "Environment configuration saved to '$ENV_PATH/environment.yaml'."
