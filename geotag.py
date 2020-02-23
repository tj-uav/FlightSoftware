from dronekit import connect, VehicleMode
import cv2
import time
import os

connection_string = '/dev/ttyACM0'
baudrate = 921600

foldername = str(time.time()).replace(".", "")
os.mkdir(foldername)

try:
    # Connect to the Vehicle.
    vehicle = connect(connection_string, wait_ready=True, baud=baudrate)
    vid = cv2.VideoCapture(0)
    i = 0
    while True:
        time.sleep(0.5)
        if os.path.isfile('endprogram.txt'):
            break
        ret, frame = vid.read()
        vid.set(3,1920)
        vid.set(4,1080)
        if not ret:
            continue
        gps = vehicle.gps_0
        i += 1

        log = open(foldername + "/log" + str(i) + ".txt", "w+")
        if gps.fix_type < 2:
            log.write("No GPS Fix\n")
            log.close()
            continue

        loc = vehicle.location.global_frame
        attitude = vehicle.attitude
        log.write("Latitude: " + str(loc.lat) + ", longitude: " + str(loc.lon) + ", altitude: " + str(loc.alt) + ", yaw$                                                                                                                                cv2.imwrite(foldername + "/frame" + str(i) + ".png", frame)
        log.close()

except:
    out = open("/home/pi/error.txt", "w+")
    out.write("ERROR REEEE: " + str(time.time()))
    out.close()
    vehicle.close()