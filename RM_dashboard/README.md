# RM Dashboard

## Overview

The RM Dashboard provides a web-based interface for monitoring the status and parameters of Truss Links (formerly Robot Links) connected to the `LinkServer`. It's designed to give a real-time overview of multiple links simultaneously, which is crucial for experiments and debugging in the Robot Metabolism project.

The dashboard is built using Dash and Flask.

## Features

* **Real-time Data Display**: Shows live data for each connected Truss Link in a sortable and filterable table.
* **Comprehensive Link Information**: Displays various parameters including:
    * Device ID and status
    * Servo positions (target and raw)
    * Battery status
    * Servo velocities
    * Maximum velocity
    * Command checksums (running vs. sent)
    * Firmware version
    * Servo calibration parameters (min/max milliseconds and raw values)
* **Video Feed (Optional)**: Includes a section for a video feed, which can be used to display a camera view or a simulation environment rendering. The `WORLD` object in `dashboard.py` needs to be assigned an object with a `draw()` method that returns an OpenCV image.
* **Threaded Operation**: Runs in a separate thread, allowing it to update independently of the main application controlling the robots.
* **Automatic Browser Launch**: Can be configured to automatically open in a web browser upon initialization.

## Dependencies

The dashboard relies on several Python packages. Ensure these are installed in your environment:

* `dash`: For creating the web application.
* `Flask`: As the web server backend for Dash.
* `opencv-python` (cv2): Used by the video feed generation (and potentially by the `world.draw()` method).
* `webbrowser`: For automatically opening the dashboard.

These are typically included in the main `requirements.txt` of the `TrussLinkServer` project.

## Setup

1.  **Parent Project Setup**: The RM Dashboard is intended to be used as part of the larger `TrussLinkServer` (formerly named `particleTrussServer`) project. Ensure the main project is set up according to its README, including cloning sub-repositories and setting up the Python environment.
2.  **Install Dependencies**: If not already done, install the required packages:
    ```bash
    pip install dash Flask opencv-python
    ```

## How to Run

The `Dashboard` class in `dashboard.py` is designed to be instantiated and run from within a script that manages the `LinkServer` (the main server communicating with the Truss Links).

**Example Usage (in your main robot control script):**

```python
# Presuming you have your LinkServer instance from linknetworking.py
# from TrussLinkServer.linknetworking import LinkServer # Adjust import path as needed
from TrussLinkServer.RM_dashboard.dashboard import Dashboard # Adjust import path

# 1. Initialize your LinkServer (example)
# link_server = LinkServer(host='', port=54657)
# ... (wait for links to connect or other setup) ...

# 2. Define which device IDs you want to monitor
device_ids_to_monitor = [1, 2, 3, 10, 14] # Example IDs

# 3. (Optional) Initialize your world/simulation object for video feed
# class MySimEnvironment:
#     def draw(self):
#         # Return an OpenCV image (numpy array)
#         import numpy as np
#         import cv2
#         img = np.zeros((480, 640, 3), dtype=np.uint8)
#         cv2.putText(img, "Simulating...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
#         return img
# sim_world = MySimEnvironment()

# 4. Instantiate and start the Dashboard
# (Pass your LinkServer instance, the list of IDs, and optionally the world instance)
# my_dashboard = Dashboard(link_server, device_ids_to_monitor, open_browser_tab=True, world_instance=sim_world)
# The dashboard will start in a new thread.

# ... (rest of your main application logic) ...

# 5. To stop (though typically the main script's termination will also stop daemon threads):
# if my_dashboard:
#    my_dashboard.close() # Note: Graceful shutdown of Flask in a thread can be complex.