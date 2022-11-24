#!/bin/bash

# Check how many images are present
NUM_FILES_IN_IMAGES = $(ls -1q /home/tjuav/FlightSoftware/assets/images | wc -l)
# If any images were saved, then save them and re-generate directory
if [ $NUM_FILES_IN_IMAGES -gt 1 ]
then
    mv /home/tjuav/FlightSoftware/assets/images/sample.png /home/tjuav/FlightSoftware/assets/sample.png
    mv /home/tjuav/FlightSoftware/assets/images "/home/tjuav/FlightSoftware/$(date +%F-%T)"
    mkdir /home/tjuav/FlightSoftware/assets/images
    mv /home/tjuav/FlightSoftware/assets/sample.png /home/tjuav/FlightSoftware/assets/images/sample.png
fi

# Activate virtual environment and run FlightSoftware
source /home/tjuav/FlightSoftware/venv/bin/activate
python /home/tjuav/FlightSoftware/main.py
