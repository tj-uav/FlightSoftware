import json
import os
import socket
import sys
from time import sleep

from dotenv import load_dotenv

sys.tracebacklimit = 0

load_dotenv()

with open("config.json", "r") as file:
    config = json.load(file)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((config["conn"]["host"], config["conn"]["port"]))
        img = os.getenv("IMAGE")  # Any sample image in base64 format
        # Spaces mark the end of the message, and therefore cannot be included in the base64 string
        # base64 strings ignore spaces, which allows space delimiters to work
        img = img.replace(" ", "")
        send = bytes(img, "utf-8") + b" "
        s.sendall(send)
        while True:
            resp = s.recv(1024)
            if not resp:
                break
            resp = resp.decode("utf-8")
            if resp == "Image Complete":  # Once image has been completely sent
                sleep(2)  # Wait two seconds to simulate delay from camera
                s.sendall(send)  # Send the same image again as a new image
except ConnectionRefusedError as e:
    raise Exception("""
FlightSoftware requires a connection to GroundStation in order to send images. \
Make sure GroundStation is running and is accepting connections. 
Clone GroundStation using any of the following commands:

    git clone -b dev git@github.com:tj-uav/GroundStation.git
    git clone -b dev https://github.com/tj-uav/GroundStation.git

Make sure to run the 'app.py' file. To start the socket connection.""") from None
