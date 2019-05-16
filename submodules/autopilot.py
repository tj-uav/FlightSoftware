import dronekit as dk
from dronekit import connect, Command, LocationGlobal, VehicleMode, LocationGlobalRelative
import mavutil

test_pwm = 1000

def set_servo(vehicle, servo_num, pwm_value):
    assert(pwm_value <= 2000)
    assert(pwm_value >= 1000)
    msg = vehicle.message_factory.command_long_encode(
    0, 0,    # target_system, target_component
    mavutil.mavlink.MAV_CMD_DO_SET_SERVO, #command
    0, #confirmation
    servo_num,    # servo number
    test_pwm,          # servo position between 1000 and 2000
    0, 0, 0, 0, 0)    # param 3 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)

def init_vehicle():
    connection_string = '/dev/ttyACM0'     #Connection used for USB
    arglist = ['parameters','gps_0','armed','mode','attitude','system_status','location']
    startime = time.time()
    log.info ("Connecting")
    vehicle = dk.connect(connection_string, wait_ready = arglist, heartbeat_timeout = 300, baud = 57600)
    log.info("Time to connection: %s" % str(time.time()-startime))

    vehicle.mode = VehicleMode("MANUAL")
    return vehicle

vehicle = init_vehicle()
set_servo(vehicle, 1, test_pwm)
set_servo(vehicle, 2, test_pwm)
set_servo(vehicle, 3, test_pwm)