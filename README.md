## Installation

Open a terminal or Anaconda Prompt with access to `conda', and follow these steps to set up the environment for the Flagging App:

1. **Update Conda:**  
   `conda update conda --yes`

2. **Create a New Conda Environment:**  
   `conda create -n flaggingapp_env python=3.10 jupyter h5py numpy pandas scipy pyyaml plotly dash --yes`

3. **Activate the Environment:**  
   `conda activate flaggingapp_env`

4. **Install Jupyter Kernel:**  
   `python -m ipykernel install --user --name flaggingapp_env --display-name "Python (flaggingapp_env)"`

5. **Install Additional Package:**  
   `pip install igor2`
