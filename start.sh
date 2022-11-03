#!/bin/bash

> /home/tjuav/FlightSoftware/stop.txt
mv /home/tjuav/FlightSoftware/assets/images/sample.png /home/tjuav/FlightSoftware/assets/sample.png
mv /home/tjuav/FlightSoftware/assets/images "/home/tjuav/FlightSoftware/$(date +%F-%T)"
mkdir /home/tjuav/FlightSoftware/assets/images
mv /home/tjuav/FlightSoftware/assets/sample.png /home/tjuav/FlightSoftware/assets/images/sample.png
python /home/tjuav/FlightSoftware/main.py
