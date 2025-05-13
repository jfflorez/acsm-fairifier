# Get additional info about the Dockerfile at https://docs.docker.com/reference/dockerfile/ 

FROM continuumio/miniconda3:latest

# Define the name of the environment
ARG ENV_NAME=apog_penv
ENV ENV_NAME=apog_penv

# Set the working directory
WORKDIR /acsmdc

#RUN apt-get update && apt-get install -y cifs-utils

# Use mamba if available for faster installation
RUN conda install -y -n base -c conda-forge mamba && \
    mamba create -y -n $ENV_NAME -c conda-forge python=3.11 \
    jupyter numpy h5py pandas matplotlib plotly=5.24 scipy pip && \
    conda clean --all -y && rm -rf /root/.cache/pip

# Activate the environment and install additional pip packages
RUN conda run -n $ENV_NAME pip install pybis==1.35 igor2 ipykernel sphinx dash dash-bootstrap-components

# Set the default environment when the container starts
ENV CONDA_DEFAULT_ENV=$ENV_NAME
ENV PATH=/opt/conda/envs/$ENV_NAME/bin:$PATH

# Create necessary directories for VOLUME
RUN mkdir -p /acsmdc/data /acsmdc/figures /acsmdc/pipelines/params
#RUN mkdir -p /mnt/lac_ord

# Copy project files, excluding certain directories (handled via .dockerignore)
COPY . /acsmdc

# Copy and install dependencies from requirements.txt
COPY requirements.txt /acsmdc/requirements.txt
RUN conda run -n $ENV_NAME pip install -r /acsmdc/requirements.txt

# Define volumes for excluded directories
VOLUME ["/acsmdc/data", "/acsmdc/figures", "/acsmdc/pipelines/params"]

# Add JupyterLab
RUN pip install --no-cache-dir jupyterlab
#RUN pip install pipx
#RUN pipx install renku
# Add any other packages needed for JupyterLab
#RUN pip install --no-cache-dir matplotlib scikit-learn

# If you want to set JupyterLab as the default command
#CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token='my-token'"]
CMD ["/bin/bash"]