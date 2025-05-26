# QC/QA Data Flagging Application

This repository hosts a Dash Plotly data flagging app for ACSM data structured in HDF5 format using the DIMA submodule. The provided Jupyter notebooks walk you through the steps to append metadata about diagnostic and target channels, which are necessary for the app to run properly.

## Getting Started

### Requirements

For Windows users, the following are required:

1. **Git Bash**: Git Bash will be used to run shell scripts (`.sh` files).

2. **Conda**: You must have [Anaconda](https://www.anaconda.com/products/individual) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed on your system. Git Bash needs access to Conda to set up the environment properly. Ensure that Conda is added to your system’s PATH during installation.

3. **PSI Network Access (for data retrieval)**: Real data retrieval can only be performed when connected to the PSI network and with the appropriate access rights to the source network drive.

## Clone the Repository

Open **Git Bash** and run:

```bash
cd GitLab
git clone --recurse-submodules https://gitea.psi.ch/APOG/acsmnode.git
cd acsmnode
```

## Run the Data Chain App

1. Open **PowerShell as Administrator** and navigate to the `acsmnode` repository.  
2. Create a `.env` file in the root of `acsmnode/`.  
3. **Securely store your network drive access credentials** in the `.env` file by adding the following lines: 
   ```plaintext
   CIFS_USER=<your-username>
   CIFS_PASS=<your-password>
   ```
   **To protect your credentials:**
   - Do not share the .env file with others.
   - Ensure the file is excluded from version control by adding .env to your .gitignore and .dockerignore files.
4. Open **Docker Desktop**, then build the container image:
   ```bash
   docker build -t datachain_processor .
   ```
5. Run the app:
   ```bash
   docker compose --file docker-compose.yaml up datachain_processor
6. Access:
   - **Jupyter Lab**: [http://localhost:8889/lab/tree/notebooks/](http://localhost:8889/lab/tree/notebooks/)

7. Stop the app:
   In the previously open PowerShell terminal, enter:
   ```bash
   Ctrl + C
   ```
   After the container is properly Stopped, remove the container process as: 
   ```bash
   docker rm $(docker ps -aq --filter ancestor=datachain_processor)
   ```

## Set Up the Python Environment

If **Git Bash** lacks a suitable Python interpreter, run:

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