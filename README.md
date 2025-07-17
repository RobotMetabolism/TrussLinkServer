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
    @article{
    doi:10.1126/sciadv.adu6897,
    author = {Philippe Martin Wyder  and Riyaan Bakhda  and Meiqi Zhao  and Quinn A. Booth  and Matthew E. Modi  and Andrew Song  and Simon Kang  and Jiahao Wu  and Priya Patel  and Robert T. Kasumi  and David Yi  and Nihar Niraj Garg  and Pranav Jhunjhunwala  and Siddharth Bhutoria  and Evan H. Tong  and Yuhang Hu  and Judah Goldfeder  and Omer Mustel  and Donghan Kim  and Hod Lipson },
    title = {Robot metabolism: Toward machines that can grow by consuming other machines},
    journal = {Science Advances},
    volume = {11},
    number = {29},
    pages = {eadu6897},
    year = {2025},
    doi = {10.1126/sciadv.adu6897},
    URL = {https://www.science.org/doi/abs/10.1126/sciadv.adu6897},
    eprint = {https://www.science.org/doi/pdf/10.1126/sciadv.adu6897},
    abstract = {Biological lifeforms can heal, grow, adapt, and reproduce, which are abilities essential for sustained survival and development. In contrast, robots today are primarily monolithic machines with limited ability to self-repair, physically develop, or incorporate material from their environments. While robot minds rapidly evolve new behaviors through artificial intelligence, their bodies remain closed systems, unable to systematically integrate material to grow or heal. We argue that open-ended physical adaptation is only possible when robots are designed using a small repertoire of simple modules. This allows machines to mechanically adapt by consuming parts from other machines or their surroundings and shed broken components. We demonstrate this principle on a truss modular robot platform. We show how robots can grow bigger, faster, and more capable by consuming materials from their environment and other robots. We suggest that machine metabolic processes like those demonstrated here will be an essential part of any sustained future robot ecology. Robots grow bigger, faster, and more capable by absorbing and integrating material in their environment.}}

    ```
