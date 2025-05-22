# Truss Link Server
Visit [https://robotmetabolism.github.io/](https://robotmetabolism.github.io/) for further Truss Link resources and links to our public GitHub repositories.

Note: Truss Link Server was formerly called ParticleTrussServer

# Python Environment
You will need a Python +3.7 environment with all the dependencies from requirements.txt installed. We show how to setup a virtual environment on Ubuntu, but you can use Anaconda or similar.

```
# Core dependencies
dash
matplotlib
numpy
opencv-python
pandas
Pillow
scipy
pynput

# Additional dependencies
contourpy
cycler
pupil-apriltags
fonttools
importlib-resources
kiwisolver
packaging
pyparsing
python-dateutil
pytz
six
tzdata
zipp
evdev
```
Note: This repository has been tested on Ubuntu 18.04. The package evdev creates a dependency conflict on OSX. The functionality of the evdev package is only used in the manualcontroller scripts to detect if num_lock is activated or deactivated to toggle between functionality. The manual controller can be modified to work without evdev. We plan to implement this change in a future itteration to add compatiblity with OSX.

## setup virtual environment (preferred option on Ubunut)
1. Create a new virtual environment `virtualenv -p /usr/bin/python3 RMenv`
2. Activate your new environment `source RMenv/bin/activate`
3. Install all dependencies `pip install -r requirements.txt`

## Experiment Conditions
Things you need before you can run a hardware experiment:
1. One or more built robot links running the TrussLinkFirmware see [https://github.com/RobotMetabolism/TrussLink](https://github.com/RobotMetabolism/TrussLink) or the Hardware directory in the data release repository
2. A WIFI network with SSID "team20_mobile" with password "robots1234" (you can alter this in the firmware)
3. Set your server's IP address (i.e. IP of the computer that runs the controller script) in the firmware code and flash your Truss Link, so the Truss Link can connect to your server. Wait until the blue LED has stopped flashing and is breathing blue (indicating a successful WIFI connection)
4. Now, run the manual controller.

## Run manual controller
1. Source the necessary PYTHONPATH configuration: `source init_project.sh` & `source RM_controllers/init_project.sh`
2. Run the manual controller with 6 robot links `python RM_controllers/manual_controller/manual_controller_v3.py 6` (alter the commnd line parameter according to the number of robot links that are connected to your local WIFI network.)
## Classes
### LinkServer

This class listens for link connections and makes Link objects which communicate with each link in a separate thread.

It contains a dictionary of all active links (with device_id as the key)

### RobotLink (represents the Truss Link)

This class is instantiated for each link, and runs in separate thread. The Latest position and vel updates are stored here.

Packages can be sent to Photon using the functions in this class.

## Support
For the latest version of this codebase, please visit: 
[TrussLinkServer repository](https://github.com/RobotMetabolism/TrussLinkServer)

## License

This project is licensed under the MIT License.

## Citation

If you use this code or draw inspiration from the associated research, please cite the following publication:

    ```bibtex
    @misc{wyder2024robotmetabolismmachinesgrow,
          title={Robot Metabolism: Towards machines that can grow by consuming other machines},
          author={Philippe Martin Wyder and Riyaan Bakhda and Meiqi Zhao and Quinn A. Booth and Matthew E. Modi and Andrew Song and Simon Kang and Jiahao Wu and Priya Patel and Robert T. Kasumi and David Yi and Nihar Niraj Garg and Pranav Jhunjhunwala and Siddharth Bhutoria and Evan H. Tong and Yuhang Hu and Judah Goldfeder and Omer Mustel and Donghan Kim and Hod Lipson},
          year={2024},
          eprint={2411.11192},
          archivePrefix={arXiv},
          primaryClass={cs.RO},
          url={[https://arxiv.org/abs/2411.11192](https://arxiv.org/abs/2411.11192)}
    }
    ```