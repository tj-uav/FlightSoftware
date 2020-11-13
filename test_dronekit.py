from dronekit import connect, VehicleMode
import cv2
import time
import os

connection_string = '/dev/ttyACM0'
baudrate = 921600

try:
    # Connect to the Vehicle.
    vehicle = connect(connection_string, wait_ready=True, baud=baudrate)
    gps = vehicle.gps_0
    if gps.fix_type < 2:
        print("No GPS Fix\n")
    print("Lat, lon, alt, yaw")
    print(loc.lat, loc.lon, loc.alt, attitude)       
except:
    out = open("error.txt", "w+")
    out.write("ERROR REEEE: " + str(time.time()))
    out.close()
finally:
    vehicle.close()