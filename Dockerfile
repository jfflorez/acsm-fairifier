# Get additional info about the Dockerfile at https://docs.docker.com/reference/dockerfile/ 

FROM continuumio/miniconda3:latest

# Define the name of the environment
ARG ENV_NAME=apog_penv
ENV ENV_NAME=apog_penv

# Set the working directory
WORKDIR /acsmdc

# Use mamba if available for faster installation
RUN conda install -y -n base -c conda-forge mamba && \
    mamba create -y -n $ENV_NAME -c conda-forge -c defaults python=3.11 \
    jupyter numpy h5py pandas matplotlib plotly=5.24 scipy pip && \
    conda clean --all -y && rm -rf /root/.cache/pip

# Activate the environment and install additional pip packages
RUN conda run -n $ENV_NAME pip install pybis==1.35 igor2 ipykernel sphinx dash dash-bootstrap-components

# Set the default environment when the container starts
ENV CONDA_DEFAULT_ENV=$ENV_NAME
ENV PATH=/opt/conda/envs/$ENV_NAME/bin:$PATH

# Create necessary directories for VOLUME
RUN mkdir -p /acsmdc/data /acsmdc/figures /acsmdc/pipelines/params

# Copy project files, excluding certain directories (handled via .dockerignore)
COPY . /

# Define volumes for excluded directories
VOLUME ["/acsmdc/data", "/acsmdc/figures", "/acsmdc/pipelines/params"]

# Default command: Run Conda shell so Python and Conda are accessible
CMD ["/bin/bash"]
