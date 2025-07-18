# Retinas (Experimental & not used in the Robot Metabolism publication)

Retinas offers 3D world reconstruction and robot link localization system for modular robots using multiple AprilTags.

## Requirements

- Ubuntu 20.04
- Python 3.8
- AprilTag 3
- 4K Camera (source code is optimized for processing 4K streams)

## Installation

Clone the repository:

    git clone https://github.com/GitWyd/RM_Retinas.git

Navigate to the cloned directory:

    cd RM_Retinas

Create a virtual environment using Python 3.8:

    python3.8 -m venv venv_name

Activate the virtual environment:

    source venv_name/bin/activate

Install the necessary dependencies:

    pip install -r requirements.txt

## Key Features

- **AprilTag Detection**: Detects AprilTags in real-time from a webcam feed.
- **Camera Calibration**: Computes the calibration matrix for the camera.
- **Pose Estimation**: Computes the 3D pose of each detected tag relative to the camera using OpenCV's solvePnP.
- **World Coordinate Transformation**: Transforms detected tag poses into a global coordinate system, defined by certain "world tags".
- **Visualization**: Displays the video feed with detected tags highlighted, showing tag ID, global pose, and reprojection error.
- **Reprojection Error Calculation**: Calculates and visualizes reprojection errors for all detected tags.

## Usage

Calibrate Your Camera:

    python src/calibration.py

Once calibration is complete, launch the main application:

## Demonstration Video

- **This video demonstrates Retinas.**
  
[![Retinas Demonstration](https://img.youtube.com/vi/BVpfQ9duoic/hqdefault.jpg)](https://youtu.be/BVpfQ9duoic)


## Notes

- The spatial relationships of the predefined world tags are hardcoded into the script. Kindly modify if your world tag setups are different.
- ELP 4KHDR01 USB Camera was used, but any 4K Camera would suffice.
