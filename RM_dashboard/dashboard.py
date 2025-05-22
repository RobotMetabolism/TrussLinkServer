"""
RM Dashboard

This module provides a web-based dashboard for monitoring Truss Links (formerly Robot Links)
connected to the LinkServer. It displays real-time data for each link,
including status, servo positions, battery levels, and more.
The dashboard uses Dash and Flask to create a web interface.

The Dashboard class is typically instantiated and run from a main controller script
that has access to the LinkServer object.
"""
import threading
import cv2
import webbrowser as wb
import logging

import dash
# Note: dash_html_components and dash_core_components are now part of dash.html and dash.dcc
from dash import html, dcc, dash_table # Updated imports
from dash.dependencies import Input, Output

from flask import Flask, Response

# Suppress Werkzeug's default INFO logs for cleaner output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Define the fields to be displayed for each link
# These correspond to attributes of the RobotLink object in linknetworking.py
FIELDS = [
    "device_id", "device_status", "srv0_pos", "srv1_pos", "srv0_raw",
    "srv1_raw", "bat_status", "srv0_vel", "srv1_vel", "MAX_VEL",
    "executing_command_checksum", "current_command_checksum", # Added for clarity from columns
    "version", "srv0_min_ms", "srv0_max_ms", "srv1_min_ms", "srv1_max_ms",
    "srv0_raw_min", "srv0_raw_max", "srv1_raw_min", "srv1_raw_max",
]

# Define the columns for the Dash DataTable
# The 'id' should match the index in the data rows, and 'name' is the displayed column header.
columns = [
    {"id": "0", "name": "Device ID"}, # Changed id to string for DataTable best practices
    {"id": "1", "name": "Status"},
    {"id": "2", "name": "Srv0 Pos"},
    {"id": "3", "name": "Srv1 Pos"},
    {"id": "4", "name": "Srv0 Raw"},
    {"id": "5", "name": "Srv1 Raw"},
    {"id": "6", "name": "Bat Status"},
    {"id": "7", "name": "Srv0 Vel"},
    {"id": "8", "name": "Srv1 Vel"},
    {"id": "9", "name": "MAX VEL"},
    {"id": "10", "name": "Running Cmd"},
    {"id": "11", "name": "Sent Cmd"},
    {"id": "12", "name": "Version"},
    {"id": "13", "name": "S0 Min ms"},
    {"id": "14", "name": "S0 Max ms"},
    {"id": "15", "name": "S1 Min ms"},
    {"id": "16", "name": "S1 Max ms"},
    {"id": "17", "name": "S0 RawMin"},
    {"id": "18", "name": "S0 RawMax"},
    {"id": "19", "name": "S1 RawMin"},
    {"id": "20", "name": "S1 RawMax"},
]

flask_server = Flask(__name__)
app = dash.Dash(__name__, server=flask_server)

# Global variable to hold the world/simulation object for video feed
# This needs to be set by the main application if a video feed is desired.
WORLD = None

@app.callback(
    [Output("table", "data"), Output('table', 'columns')],
    [Input("table-update", "n_intervals")]
)
def update_table(n_intervals):
    """
    Callback function to update the data table at regular intervals.
    Fetches the latest link data from the Dashboard instance.
    """
    if Dashboard.DASHBOARD_INSTANCE: # Check if instance exists
        return Dashboard.DASHBOARD_INSTANCE.get_rows(), columns
    return [], columns # Return empty data if dashboard not initialized

def gen_video_feed(world_obj):
    """
    Generator function for the video feed.
    If a 'world_obj' with a 'draw' method is provided, it yields JPEG frames.
    """
    while True:
        if world_obj and hasattr(world_obj, 'draw'):
            frame = world_obj.draw() # Assuming world_obj.draw() returns an OpenCV image
            if frame is not None:
                _, jpeg_frame = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_frame.tobytes() + b'\r\n\r\n')
            else:
                # Yield a placeholder or wait if no frame is available
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + b'\r\n\r\n')
                cv2.waitKey(100) # Adjust delay as needed
        else:
            # Yield a placeholder or wait if WORLD is not set
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + b'\r\n\r\n')
            cv2.waitKey(100) # Adjust delay as needed


@flask_server.route('/video_feed')
def video_feed_route():
    """
    Flask route to serve the video feed.
    """
    return Response(gen_video_feed(WORLD),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

class Dashboard(threading.Thread):
    """
    Dashboard class to display Truss Link information.
    Runs a Dash application in a separate thread.
    """
    DASHBOARD_INSTANCE = None # Class variable to hold the active instance

    def __init__(self, server_instance, device_ids_to_monitor, open_browser_tab=False, world_instance=None):
        """
        Initializes the Dashboard.

        Args:
            server_instance: The LinkServer instance managing the Truss Links.
            device_ids_to_monitor: A list of device IDs to display in the dashboard.
            open_browser_tab (bool): Whether to automatically open the dashboard in a new browser tab.
            world_instance: An optional object (e.g., a simulation environment) that has a `draw()`
                            method returning an OpenCV image for the video feed.
        """
        super().__init__()
        self.link_server = server_instance
        self.device_ids = device_ids_to_monitor
        self.open_browser = open_browser_tab
        self.__is_running = True
        Dashboard.DASHBOARD_INSTANCE = self # Set the active instance

        global WORLD
        WORLD = world_instance

        # Daemonize the thread so it exits when the main program exits
        self.daemon = True


    def run(self):
        """
        Starts the Dash application server.
        """
        # app.scripts.config.serve_locally = True # Deprecated

        app.layout = html.Div(children=[
            html.H1("Truss Link Dashboard"),
            html.Div([
                dash_table.DataTable(
                    id='table',
                    columns=columns, # Set columns here
                    data=self.get_rows(), # Initial data
                    style_cell={'textAlign': 'left', 'padding': '5px'},
                    style_header={
                        'backgroundColor': 'lightgrey',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ]
                ),
                dcc.Interval(
                    id='table-update',
                    interval=250,  # Milliseconds
                    n_intervals=0
                ),
            ]),
            html.H2("Video Feed (Optional)"),
            html.Img(src="/video_feed", style={'width': '640px', 'height': '480px', 'border': '1px solid black'})
        ])

        if self.open_browser:
            # Wait a moment for the server to start before opening the browser
            threading.Timer(1.5, lambda: webbrowser.open("http://localhost:8053/", new=2)).start()

        print("Starting Dashboard server on http://localhost:8053/")
        app.run_server(port=8053, debug=False, use_reloader=False) # use_reloader=False for threads

    def close(self):
        """
        Stops the dashboard.
        Note: Properly stopping a Flask/Dash server run in a thread is non-trivial.
        This method signals the thread to stop, but server shutdown might need external handling.
        """
        self.__is_running = False
        print("Dashboard close method called. Manual server stop might be required.")
        # For a more graceful shutdown, you might need to look into Flask's capabilities
        # or use a different approach for running the server if programmatic stop is essential.

    def get_rows(self):
        """
        Fetches and formats the data for the connected Truss Links.

        Returns:
            A list of dictionaries, where each dictionary represents a row in the table.
        """
        rows = []
        if not self.link_server or not hasattr(self.link_server, 'links'):
            return []

        for device_id in self.device_ids:
            if device_id in self.link_server.links:
                link = self.link_server.links[device_id]
                # Ensure all FIELDS are attributes of the link object
                row_data = {
                    "0": link.device_id,
                    "1": getattr(link, 'device_status', 'N/A'),
                    "2": getattr(link, 'srv0_pos', 'N/A'),
                    "3": getattr(link, 'srv1_pos', 'N/A'),
                    "4": getattr(link, 'srv0_raw', 'N/A'),
                    "5": getattr(link, 'srv1_raw', 'N/A'),
                    "6": getattr(link, 'bat_status', 'N/A'),
                    "7": getattr(link, 'srv0_vel', 'N/A'),
                    "8": getattr(link, 'srv1_vel', 'N/A'),
                    "9": getattr(link, 'MAX_VEL', 'N/A'),
                    "10": str(getattr(link, 'executing_command_checksum', 'N/A')),
                    "11": str(getattr(link, 'current_command_checksum', 'N/A')),
                    "12": getattr(link, 'version', 'N/A'),
                    "13": getattr(link, 'srv0_min_ms', 'N/A'),
                    "14": getattr(link, 'srv0_max_ms', 'N/A'),
                    "15": getattr(link, 'srv1_min_ms', 'N/A'),
                    "16": getattr(link, 'srv1_max_ms', 'N/A'),
                    "17": getattr(link, 'srv0_raw_min', 'N/A'),
                    "18": getattr(link, 'srv0_raw_max', 'N/A'),
                    "19": getattr(link, 'srv1_raw_min', 'N/A'),
                    "20": getattr(link, 'srv1_raw_max', 'N/A'),
                }
                rows.append(row_data)
        # Simple sort by device_id if needed, converting to int for proper numeric sort
        try:
            rows = sorted(rows, key=lambda x: int(x["0"]))
        except ValueError:
            # Handle cases where device_id might not be purely numeric or 'N/A'
            rows = sorted(rows, key=lambda x: str(x["0"]))
        return rows

if __name__ == '__main__':
    # This is an example of how to run the dashboard standalone.
    # In a real application, you would integrate it with your LinkServer.

    # Mock LinkServer and RobotLink for testing
    class MockRobotLink:
        def __init__(self, device_id):
            self.device_id = device_id
            self.device_status = "Nominal"
            self.srv0_pos = 50
            self.srv1_pos = 50
            self.srv0_raw = 1500
            self.srv1_raw = 1500
            self.bat_status = 99
            self.srv0_vel = 0
            self.srv1_vel = 0
            self.MAX_VEL = 100
            self.executing_command_checksum = "0xFFFF"
            self.current_command_checksum = "0xFFFF"
            self.version = "1.0"
            self.srv0_min_ms = 1000
            self.srv0_max_ms = 2000
            self.srv1_min_ms = 1000
            self.srv1_max_ms = 2000
            self.srv0_raw_min = 0
            self.srv0_raw_max = 1023
            self.srv1_raw_min = 0
            self.srv1_raw_max = 1023

    class MockLinkServer:
        def __init__(self):
            self.links = {
                1: MockRobotLink(1),
                2: MockRobotLink(2),
                10: MockRobotLink(10)
            }
    
    class MockWorld: # For video feed testing
        def __init__(self):
            self.frame_counter = 0
        def draw(self):
            self.frame_counter +=1
            # Create a blank image with a frame counter
            img = cv2.UMat(np.zeros((480, 640, 3), dtype=np.uint8)).get() # Ensure UMat is converted to numpy array
            cv2.putText(img, f"Frame: {self.frame_counter}", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            return img


    mock_server = MockLinkServer()
    mock_world = MockWorld() # Create an instance of MockWorld

    # Example device IDs to monitor
    device_ids_to_show = [1, 2, 5, 10] # Link 5 won't be in mock_server.links

    print("Starting standalone RM_Dashboard example...")
    # The Dashboard will run in a separate thread.
    dashboard_instance = Dashboard(mock_server, device_ids_to_show, open_browser_tab=True, world_instance=mock_world)

    # Keep the main thread alive, e.g., by waiting for user input or running other tasks.
    try:
        while True:
            # Update mock data for testing dynamic updates (optional)
            mock_server.links[1].srv0_pos = (mock_server.links[1].srv0_pos + 1) % 100
            cv2.waitKey(1000) # Simulate work in the main thread
    except KeyboardInterrupt:
        print("Stopping dashboard example...")
        if dashboard_instance:
            dashboard_instance.close()
    print("Dashboard example finished.")