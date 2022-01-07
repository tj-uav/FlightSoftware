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

print("""--------------------
FlightSoftware requires a connection to GroundStation in order to send images. \
Make sure GroundStation is running and is accepting connections. 
Clone GroundStation using any of the following commands:

    git clone -b dev git@github.com:tj-uav/GroundStation.git
    git clone -b dev https://github.com/tj-uav/GroundStation.git

Make sure to run the 'app.py' file to start the socket connection.
--------------------
""")

while True:  # Attempts to re-initiate connection on connection loss
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((config["conn"]["host"], config["conn"]["port"]))
            print("[SUCCESS] Connected to GroundStation")
            img = os.getenv("IMAGE")  # Any sample image in base64 format
            # Spaces mark the end of the message, and therefore cannot be included in the base64 string
            # base64 strings ignore spaces, which allows space delimiters to work
            img = img.replace(" ", "")
            send = bytes(img, "utf-8") + b" "
            s.sendall(send)
            while True:
                resp = s.recv(4096)
                if not resp:
                    print("""[ ERROR ] Connection to GroundStation was closed, possibly due to program termination. FlightSoftware is attempting to re-initiate a connection.""")
                    break
                resp = resp.decode("utf-8")
                if resp == "Image Complete":  # Once image has been completely sent
                    sleep(2)  # Wait two seconds to simulate delay from camera
                    s.sendall(send)  # Send the same image again as a new image
    except ConnectionRefusedError as e:
        print("[ ERROR ] Connection Refused: Make sure GroundStation is running and accepting connections")
    sleep(5)
