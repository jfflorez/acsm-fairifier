#!/bin/bash

# Define the name of the environment
ENV_NAME="multiphase_chemistry_env"

# Check if mamba is available and use it instead of conda for faster installation
if command -v mamba &> /dev/null; then
    CONDA_COMMAND="mamba"
else
    CONDA_COMMAND="conda"
fi

# Create the conda environment with all dependencies, resolving from conda-forge and defaults
$CONDA_COMMAND create -y -n "$ENV_NAME" -c conda-forge -c defaults python=3.11 \
    jupyter numpy h5py pandas matplotlib plotly=5.24 scipy pip

# Check if the environment was successfully created
if [ $? -ne 0 ]; then
    echo "Failed to create the environment '$ENV_NAME'. Please check the logs above for details."
    exit 1
fi

# Activate the new environment
if source activate "$ENV_NAME" 2>/dev/null || conda activate "$ENV_NAME" 2>/dev/null; then
    echo "Environment '$ENV_NAME' activated successfully."
else
    echo "Failed to activate the environment '$ENV_NAME'. Please check your conda setup."
    exit 1
fi

# Install additional pip packages only if the environment is activated
echo "Installing additional pip packages..."
pip install pybis==1.35 igor2 ipykernel sphinx
pip install dash dash-bootstrap-components

# Check if pip installations were successful
if [ $? -ne 0 ]; then
    echo "Failed to install pip packages. Please check the logs above for details."
    exit 1
fi

# Optional: Export the environment to a YAML file (commented out)
# $CONDA_COMMAND env export -n "$ENV_NAME" > "$ENV_NAME-environment.yaml"

# Print success message
echo "Environment '$ENV_NAME' created and configured successfully."
# echo "Environment configuration saved to '$ENV_NAME-environment.yaml'."

