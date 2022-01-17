import base64
import json
import os
import socketio
import sys
import cv2 as cv

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

WIDTH = config["image"]["width"]
HEIGHT = config["image"]["height"]


def dummy_send_images():
    while True:
        img = os.getenv("IMAGE")
        try:
            sio.emit("image", {"image": img})
        except:
            pass
        sio.sleep(2)


def send_images():
    cam = cv.VideoCapture(config["image"]["device"])  # , cv.CAP_DSHOW)
    cam.set(3, WIDTH)
    cam.set(4, HEIGHT)
    img_counter = 0
    img_send_counter = 0
    while True:
        sio.sleep(2)
        ret, frame = cam.read()
        if not ret:
            print("[ ERROR ] Failed to grab frame from camera")
            continue
        try:
            ret, buffer = cv.imencode(".png", frame)
            b64 = base64.b64encode(buffer)
            sio.emit("image", {"image": b64})
            while img_send_counter < img_counter:
                with open(f"images/image_{img_send_counter}.jpg", "rb") as img_file:
                    encoded = base64.b64encode(img_file.read())
                    sio.emit("image", {"image": encoded})
                print(f"[ INFO  ] Image file \"image_{img_send_counter}.jpg\" sent to GroundStation")
                img_send_counter += 1
        except:
            cv.imwrite(f"images/image_{img_counter}.jpg", frame)
            print(f"[ INFO  ] Image written to file: \"image_{img_counter}.jpg\"")
            img_counter += 1
    cam.release()


@sio.event
def connect():
    print("[SUCCESS] Connected to GroundStation with sid:", sio.sid)


@sio.event
def connect_error(_):
    print("[ ERROR ] Connection Refused: Make sure GroundStation is running and accepting connections.")


@sio.event
def disconnect():
    print("[ ERROR ] Connection to GroundStation was closed, possibly due to program termination. FlightSoftware is attempting to re-initiate a connection.")


sio.connect(f"http://{config['groundstation']['host']}:{config['groundstation']['port']}")

target = dummy_send_images if config["image"]["dummy"] else send_images
sio.start_background_task(target=target)
