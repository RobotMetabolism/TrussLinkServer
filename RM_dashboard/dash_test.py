"""
Dash Video Streaming Test

This script demonstrates a simple Dash application that streams video
from a webcam. It uses Flask for the backend video feed.

To run this script:
1. Ensure you have Dash, Flask, and OpenCV installed.
   (pip install dash flask opencv-python)
2. Execute the script: python dash_test.py
3. Open your web browser to http://localhost:8050 (or the port specified).
"""
import dash
# Note: dash_core_components and dash_html_components are now part of dash.dcc and dash.html
from dash import dcc, html # Updated imports
from flask import Flask, Response
import cv2

class VideoCamera:
    """
    A simple class to handle video capturing from a webcam.
    """
    def __init__(self, camera_index=0):
        """
        Initializes the video capture.

        Args:
            camera_index (int): The index of the camera to use (default is 0).
        """
        self.video = cv2.VideoCapture(camera_index)
        if not self.video.isOpened():
            raise RuntimeError(f"Could not start camera at index {camera_index}.")
        print(f"Camera {camera_index} opened successfully.")

    def __del__(self):
        """
        Releases the video capture when the object is deleted.
        """
        if self.video.isOpened():
            self.video.release()
        print("Video camera released.")

    def get_frame(self):
        """
        Captures a single frame from the webcam, encodes it as JPEG,
        and returns it as bytes.

        Returns:
            bytes: The JPEG encoded frame. Returns None if frame capture fails.
        """
        success, image = self.video.read()
        if not success:
            print("Failed to capture frame.")
            return None
        
        # Encode frame as JPEG
        ret, jpeg = cv2.imencode('.jpg', image)
        if not ret:
            print("Failed to encode frame to JPEG.")
            return None
        return jpeg.tobytes()

def gen(camera):
    """
    A generator function that continuously yields frames from the camera
    for video streaming.

    Args:
        camera (VideoCamera): An instance of the VideoCamera class.
    """
    while True:
        frame_bytes = camera.get_frame()
        if frame_bytes is None:
            # If a frame can't be grabbed, send an empty frame or break.
            # For simplicity, we'll just wait and try again.
            cv2.waitKey(100) # Adjust delay as needed
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

# Initialize Flask server and Dash app
flask_server = Flask(__name__)
app = dash.Dash(__name__, server=flask_server)

# Global VideoCamera instance
# This is created once to avoid reinitializing the camera on every request.
# You might want to handle camera selection more robustly in a real app.
try:
    video_camera_instance = VideoCamera(0)
except RuntimeError as e:
    print(f"Error initializing camera: {e}")
    video_camera_instance = None


@flask_server.route('/video_feed')
def video_feed():
    """
    Flask route that serves the video stream.
    """
    if video_camera_instance is None:
        return "Error: Camera not available.", 500
    return Response(gen(video_camera_instance),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Define the layout of the Dash application
app.layout = html.Div([
    html.H1("Webcam Test Feed"),
    html.P("This page streams video from your default webcam (index 0)."),
    html.Img(src="/video_feed", style={'width': '640px', 'height': '480px', 'border': '1px solid black'})
])

if __name__ == '__main__':
    print("Starting Dash application on http://localhost:8050/")
    app.run_server(debug=True, port=8050) # Changed default port to avoid conflict with main dashboard