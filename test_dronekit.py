from dronekit import connect, VehicleMode

import time
import os

connection_string = '/dev/ttyACM0'
baudrate = 115200

# Connect to the Vehicle.
vehicle = connect(connection_string, wait_ready=True, baud=baudrate)
loc = vehicle.location.global_frame
gps = vehicle.gps_0
attitude = vehicle.attitude
if gps.fix_type < 2:
	print("No GPS Fix\n")
print(loc)
print(attitude)
vehicle.close()