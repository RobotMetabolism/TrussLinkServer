# RM_controllers
Robot Metabolism Controller Scripts that can be executed with command line flags for either simulation or physical robot experiments.

# Setup
1. Clone the RM_controllers repository inside your TrussLinkServer folder
2. Navigate into the newly cloned folder: `cd RM_controllers`
4. Move on to creating the Virtual Environment containing all the necessary packages

## Virtual Env Setup
1. Create the "RMenv" virtual environment: adjust the line '/usr/bin/python3.X' to match your python version
virtualenv -p /usr/bin/python3.6 RMenv

2. Initialize the "RMenv"
source RMenv/bin/activate

3. Install necessary packages using pip
pip install -r requirements.txt
