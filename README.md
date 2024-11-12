# QC/QA Data Flagging Application

This repository hosts a Dash Plotly data flagging app for ACSM data structured in HDF5 format using the DIMA submodule. The provided Jupyter notebooks walk you through the steps to append metadata about diagnostic and target channels, which are necessary for the app to run properly.

## Getting Started

### Requirements

For Windows users, the following are required:

1. **Git Bash**: Git Bash will be used to run shell scripts (`.sh` files).

2. **Conda**: You must have [Anaconda](https://www.anaconda.com/products/individual) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed on your system. Git Bash needs access to Conda to set up the environment properly. Ensure that Conda is added to your system’s PATH during installation.

3. **PSI Network Access (for data retrieval)**: Real data retrieval can only be performed when connected to the PSI network and with the appropriate access rights to the source network drive.

## Clone the Repository

Open a **Git Bash** terminal.

1. Navigate to your GitLab folder, clone the repository, and navigate to the `acsmnode` folder:

   ```bash
   cd GitLab
   git clone --recurse-submodules https://gitlab.psi.ch/apog/acsmnode.git
   cd acsmnode
   ```

### Set Up the Python Environment

Skip this step if the **Git Bash** terminal already has access to a suitable Python interpreter.

Otherwise, set up an appropriate Python interpreter by running the following command:

   ```bash
   bash env_setup.sh
   ```


## Run the Dashboard App
Run the following command to start the dashboard app:

   ```bash
   python data_flagging_app.py
   ```

This command will launch the data flagging app.

## Stop the Dashboard App

Run the following command to stop the dashboard app:

   ```bash
   CTRL + C
   ```
This command will terminate the server process running the app.