#!/bin/bash

# Clone FlightSoftware
#git clone https://github.com/tj-uav/FlightSoftware.git
#cd FlightSoftware

# Install dependencies
sudo apt install libgphoto2-dev -y

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy config file
cp sample.config.json config.json

# Create and enable the systemd service
sudo cp flightsoftware.service /etc/systemd/system/flightsoftware.service
sudo systemctl enable flightsoftware.service

# Configure network for ethernet
sudo cp dhcpcd.conf /etc/dhcpcd.conf
