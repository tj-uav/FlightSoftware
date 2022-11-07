#!/bin/bash

git clone https://github.com/tj-uav/FlightSoftware.git
cd FlightSoftware

sudo apt install libgphoto2-dev

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp sample.config.json config.json

sudo cp flightsoftware.service /etc/systemd/system/flightsoftware.service

sudo systemctl enable flightsoftware.service

sudo cp dhcpcd.conf /etc/dhcpcd.conf
