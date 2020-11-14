from dronekit import connect, VehicleMode

import time
import os

connection_string = '/dev/ttyUSB0'
baudrate = 115200

# Connect to the Vehicle.
vehicle = connect(connection_string, wait_ready=True, baud=baudrate)
gps = vehicle.gps_0
if gps.fix_type < 2:
	print("No GPS Fix\n")
print("Lat, lon, alt, yaw")
print(loc.lat, loc.lon, loc.alt, attitude)
vehicle.close()
