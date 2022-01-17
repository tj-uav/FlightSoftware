import json
import os
import socketio
import sys
import requests

from dotenv import load_dotenv

sys.tracebacklimit = 0

load_dotenv()

with open("config.json", "r") as file:
    config = json.load(file)

print("""--------------------
FlightSoftware requires a connection to GroundStation in order to send images. \
Make sure GroundStation is running and is accepting connections. 
Clone GroundStation using any of the following commands:

    git clone git@github.com:tj-uav/GroundStation.git
    git clone https://github.com/tj-uav/GroundStation.git

Make sure to run the 'app.py' file to start the socket connection.
--------------------
""")

sio = socketio.Client()


def send_image_loop():
    while True:
        img = os.getenv("IMAGE")
        try:
            sio.emit("image", {"image": img})
        except:
            pass
        sio.sleep(2)


@sio.event
def connect():
    print("[SUCCESS] Connected to GroundStation with sid:", sio.sid)
    sio.start_background_task(target=send_image_loop)


@sio.event
def connect_error(_):
    print("[ ERROR ] Connection Refused: Make sure GroundStation is running and accepting connections.")


@sio.event
def disconnect():
    print("[ ERROR ] Connection to GroundStation was closed, possibly due to program termination. FlightSoftware is attempting to re-initiate a connection.")


sio.connect(f"http://{config['groundstation']['host']}:{config['groundstation']['port']}")
