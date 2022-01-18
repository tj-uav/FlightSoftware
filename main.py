import base64
import json
import os
import sys
import time
from threading import Thread

import cv2 as cv
import gpiozero
import socketio
from dotenv import load_dotenv

print("""--------------------
FlightSoftware requires a connection to GroundStation in order to send images. \
Make sure GroundStation is running and is accepting connections. 
Clone GroundStation using any of the following commands:

    git clone git@github.com:tj-uav/GroundStation.git
    git clone https://github.com/tj-uav/GroundStation.git

Make sure to run the 'app.py' file to start the socket connection.
--------------------
""")

sys.tracebacklimit = 0

load_dotenv()

with open("config.json", "r") as file:
    config = json.load(file)

WIDTH = config["image"]["width"]
HEIGHT = config["image"]["height"]

img_counter = 0
img_send_counter = 0

existing_files = len([name for name in os.listdir("images") if os.path.isfile(os.path.join("images", name)) and name.endswith(".png")])
if existing_files > 1:
    img_counter = existing_files - 1
    img_send_counter = existing_files - 1

button = None if config["gimbal"]["dummy"] else gpiozero.Button(config["gimbal"]["pin"], pull_up=False)


def take_images(sock):
    global img_counter
    cam = cv.VideoCapture(config["image"]["device"])  # , cv.CAP_DSHOW)
    cam.set(3, WIDTH)
    cam.set(4, HEIGHT)
    while True:
        sock.sleep(0.5)
        if not config["gimbal"]["dummy"] and not button.is_pressed:  # If the gimbal exists and is not ready to take pictures
            print("[ INFO  ] Waiting for confirmation from gimbal")
            continue  # Wait longer
        ret, frame = cam.read()
        if not ret:
            print("[ ERROR ] Failed to grab frame from camera")
            continue
        print(f"[ INFO  ] {img_counter} saving...")
        cv.imwrite(f"images/image_{img_counter}_100.jpg", frame, [int(cv.IMWRITE_JPEG_QUALITY), 100])
        cv.imwrite(f"images/image_{img_counter}_095.jpg", frame, [int(cv.IMWRITE_JPEG_QUALITY), 95])
        cv.imwrite(f"images/image_{img_counter}_090.jpg", frame, [int(cv.IMWRITE_JPEG_QUALITY), 90])
        cv.imwrite(f"images/image_{img_counter}_075.jpg", frame, [int(cv.IMWRITE_JPEG_QUALITY), 75])
        cv.imwrite(f"images/image_{img_counter}_050.jpg", frame, [int(cv.IMWRITE_JPEG_QUALITY), 50])
        cv.imwrite(f"images/image_{img_counter}.bmp", frame)
        cv.imwrite(f"images/image_{img_counter}.png", frame)
        print(f"[ INFO  ] {img_counter} saved.")
        img_counter += 1


def dummy_take_images(sock):
    global img_counter
    img = os.getenv("IMAGE")
    while True:
        sock.sleep(1.1)  # Account for delay in saving images
        with open(f"images/image_{img_counter}.png", "wb") as image_file:
            image_file.write(base64.b64decode(img))
        print(f"[ INFO  ] {img_counter} saved.")
        img_counter += 1


def send_images(sock):
    global img_send_counter
    while True:
        sock.sleep(1)  # Delay for one second before sending images
        try:
            if img_send_counter < img_counter:
                with open(f"images/image_{img_send_counter}.png", "rb") as image_file:
                    img = base64.b64encode(image_file.read())
                    sock.emit("image", {"image": img})
                print(f"[ INFO  ] {img_send_counter} sent!")
                img_send_counter += 1
        except:
            pass


def dummy_send_images():
    global img_send_counter
    while True:
        time.sleep(1)
        if img_send_counter < img_counter:
            print(f"[ INFO  ] {img_send_counter} sent!")
            img_send_counter += 1


if config["groundstation"]["dummy"]:
    take = dummy_take_images if config["image"]["dummy"] else take_images
    take_t = Thread(target=take, args=(time,))
    send_t = Thread(target=dummy_send_images)
    take_t.start()
    send_t.start()
else:
    sio = socketio.Client()

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

    take = dummy_take_images if config["image"]["dummy"] else take_images
    sio.start_background_task(take, sio)
    sio.start_background_task(send_images, sio)
