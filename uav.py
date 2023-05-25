from __future__ import annotations
import logging
import math

from dronekit import connect, Command, VehicleMode, Vehicle

from utils.errors import GeneralError
from utils.decorators import decorate_all_functions, log

BAUDRATE = 57600


def pixhawk_stats(vehicle):
    vehicle.wait_ready("autopilot_version")
    print("\nGet all vehicle attribute values:")
    print(f" Autopilot Firmware version: {vehicle.version}")
    print(f"   Major version number: {vehicle.version.major}")
    print(f"   Minor version number: {vehicle.version.minor}")
    print(f"   Patch version number: {vehicle.version.patch}")
    print(f"   Release type: {vehicle.version.release_type()}")
    print(f"   Release version: {vehicle.version.release_version()}")
    print(f"   Stable release?: {vehicle.version.is_stable()}")
    print(" Autopilot capabilities")
    print(f"   Supports MISSION_FLOAT message type: {vehicle.capabilities.mission_float}")
    print(f"   Supports PARAM_FLOAT message type: {vehicle.capabilities.param_float}")
    print(f"   Supports MISSION_INT message type: {vehicle.capabilities.mission_int}")
    print(f"   Supports COMMAND_INT message type: {vehicle.capabilities.command_int}")
    print(f"   Supports PARAM_UNION message type: {vehicle.capabilities.param_union}")
    print(f"   Supports ftp for file transfers: {vehicle.capabilities.ftp}")
    print(f"   Supports commanding attitude offboard: {vehicle.capabilities.set_attitude_target}")
    print(
        f"   Supports commanding position and velocity targets in local NED frame: {vehicle.capabilities.set_attitude_target_local_ned}"
    )
    print(
        f"   Supports set position + velocity targets in global scaled integers: {vehicle.capabilities.set_altitude_target_global_int}"
    )
    print(f"   Supports terrain protocol / data handling: {vehicle.capabilities.terrain}")
    print(f"   Supports direct actuator control: {vehicle.capabilities.set_actuator_target}")
    print(f"   Supports the flight termination command: {vehicle.capabilities.flight_termination}")
    print(f"   Supports mission_float message type: {vehicle.capabilities.mission_float}")
    print(f"   Supports onboard compass calibration: {vehicle.capabilities.compass_calibration}")
    print(f" Global Location: {vehicle.location.global_frame}")
    print(f" Global Location (relative altitude): {vehicle.location.global_relative_frame}")
    print(f" Local Location: {vehicle.location.local_frame}")
    print(f" Attitude: {vehicle.attitude}")
    print(f" Velocity: {vehicle.velocity}")
    print(f" GPS: {vehicle.gps_0}")
    print(f" Gimbal status: {vehicle.gimbal}")
    print(f" Battery: {vehicle.battery}")
    print(f" EKF OK?: {vehicle.ekf_ok}")
    print(f" Last Heartbeat: {vehicle.last_heartbeat}")
    print(f" Rangefinder: {vehicle.rangefinder}")
    print(f" Rangefinder distance: {vehicle.rangefinder.distance}")
    print(f" Rangefinder voltage: {vehicle.rangefinder.voltage}")
    print(f" Heading: {vehicle.heading}")
    print(f" Is Armable?: {vehicle.is_armable}")
    print(f" System status: {vehicle.system_status.state}")
    print(f" Groundspeed: {vehicle.groundspeed}")  # settable
    print(f" Airspeed: {vehicle.airspeed}")  # settable
    print(f" Mode: {vehicle.mode.name}")  # settable
    print(f" Armed: {vehicle.armed}")  # settable


def readmission(filename):
    """
    Load a mission from a file into a list.

    This function is used by upload_mission().
    """
    print(f"Reading mission from file: {filename}\n")
    missionlist = []
    with open(filename, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                if not line.startswith("QGC WPL 110"):
                    raise Exception("File is not supported WP version")
            else:
                linearray = line.split("\t")
                ln_currentwp = int(linearray[1])
                ln_frame = int(linearray[2])
                ln_command = int(linearray[3])
                ln_param1 = float(linearray[4])
                ln_param2 = float(linearray[5])
                ln_param3 = float(linearray[6])
                ln_param4 = float(linearray[7])
                ln_param5 = float(linearray[8])
                ln_param6 = float(linearray[9])
                ln_param7 = float(linearray[10])
                ln_autocontinue = int(linearray[11].strip())
                cmd = Command(
                    0,
                    0,
                    0,
                    ln_frame,
                    ln_command,
                    ln_currentwp,
                    ln_autocontinue,
                    ln_param1,
                    ln_param2,
                    ln_param3,
                    ln_param4,
                    ln_param5,
                    ln_param6,
                    ln_param7,
                )
                missionlist.append(cmd)
    return missionlist


def download_mission(vehicle):
    """
    Downloads the current mission and returns it in a list.
    It is used in save_mission() to get the file information to save.
    """
    missionlist = []
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()
    for cmd in cmds:
        missionlist.append(cmd)
    return missionlist


@decorate_all_functions(log, logging.getLogger("groundstation"))
class UAVHandler:
    mps_to_mph = 2.23694
    m_to_ft = 3.28084

    wait_for = ("gps_0", "armed", "mode", "attitude")  # params

    def __init__(self, config):
        self.logger = logging.getLogger("uav")
        self.config = config
        self.port = self.config["uav"]["port"]
        self.update_thread = None
        self.vehicle: Vehicle | None = None
        (
            self.altitude,
            self.altitude_global,
            self.orientation,
            self.ground_speed,
            self.air_speed,
            self.dist_to_wp,
            self.dist_to_home,
            self.battery,
            self.home,
            self.lat,
            self.lon,
            self.connection,
            self.waypoint,
            self.waypoints,
            self.waypoint_index,
            self.temperature,
            self.params,
            self.gps,
            self.servo_outputs,
        ) = [None] * 19
        self.mode = VehicleMode("MANUAL")
        self.commands = []
        self.armed = False
        self.status = "STANDBY"
        print("╠ CREATED UAV HANDLER")
        self.logger.info("CREATED UAV HANDLER")

    # Basic Methods

    def connect(self):
        try:
            self.vehicle = connect(self.port, wait_ready=self.wait_for, baud=BAUDRATE)
            pixhawk_stats(self.vehicle)
            self.make_listeners()
            self.update()
            print("╠ INITIALIZED UAV HANDLER")
            self.logger.info("INITIALIZED UAV HANDLER")
            return {}
        except Exception as e:
            raise GeneralError(str(e)) from e

    def make_listeners(self):
        self.battery = [0, 0]
        self.servo_outputs = []

        @self.vehicle.on_message("BATTERY_STATUS")
        def battery_status_listener(_v, _n, message):
            battery_id = message.id
            battery_voltage = message.voltages[0]
            self.battery[battery_id] = battery_voltage * 0.001  # mV to V

        @self.vehicle.on_message("SERVO_OUTPUT_RAW")
        def servo_output_raw_listener(_v, _n, message):
            self.servo_outputs = [
                message.servo1_raw,
                message.servo2_raw,
                message.servo3_raw,
                message.servo4_raw,
                message.servo5_raw,
                message.servo6_raw,
                message.servo7_raw,
                message.servo8_raw,
                message.servo9_raw,
            ]

    def update(self):
        try:
            # Global Relative Frame uses absolute Latitude/Longitude and relative Altitude
            loc = self.vehicle.location.global_relative_frame
            rpy = self.vehicle.attitude  # Roll, Pitch, Yaw
            self.altitude = loc.alt * self.m_to_ft
            self.altitude_global = self.vehicle.location.global_frame.alt * self.m_to_ft
            self.orientation = dict(
                yaw=rpy.yaw * 180 / math.pi,
                roll=rpy.roll * 180 / math.pi,
                pitch=rpy.pitch * 180 / math.pi,
            )
            self.orientation["yaw"] += 360 if self.orientation["yaw"] < 0 else 0
            self.ground_speed = self.vehicle.groundspeed * self.mps_to_mph
            self.air_speed = self.vehicle.airspeed * self.mps_to_mph
            self.gps = self.vehicle.gps_0
            self.connection = [self.gps.eph, self.gps.epv, self.gps.satellites_visible]
            self.home = {
                "lat": self.vehicle.home_location.lat,
                "lon": self.vehicle.home_location.lon,
            }
            self.lat = loc.lat
            self.lon = loc.lon
            self.waypoint_index = self.vehicle.commands.next - 1
            try:
                self.waypoint = self.vehicle.commands[self.waypoint_index]
                x_dist_to_wp = (
                    (self.waypoint.x - self.lat)
                    * (math.cos(self.lat * math.pi / 180) * 69.172)
                    * 5280
                )
                y_dist_to_wp = (self.waypoint.y - self.lon) * 69.172 * 5280
                self.dist_to_wp = math.sqrt(x_dist_to_wp**2 + y_dist_to_wp**2)
            except IndexError:
                self.dist_to_wp = -1
            x_dist_to_home = (
                (self.home["lat"] - self.lat) * (math.cos(self.lat * math.pi / 180) * 69.172) * 5280
            )
            y_dist_to_home = (self.home["lon"] - self.lon) * 69.172 * 5280
            self.dist_to_home = math.sqrt(x_dist_to_home**2 + y_dist_to_home**2)
            self.waypoint = [self.waypoint_index, self.dist_to_wp]
            self.mode = self.vehicle.mode
            self.armed = self.vehicle.armed
            return {}
        except Exception as e:
            raise GeneralError(str(e)) from e

    def location(self):
        try:
            return {
                "lat": self.lat,
                "lon": self.lon,
                "alt": self.altitude,
                "altg": self.altitude_global,
                "heading": self.orientation["yaw"],
            }
        except Exception as e:
            raise GeneralError(str(e)) from e

    def quick(self):
        try:
            self.update()
            return {
                "result": {
                    "altitude": self.altitude,
                    "altitude_global": self.altitude_global,
                    "orientation": self.orientation,
                    "home": self.home,
                    "lat": self.lat,
                    "lon": self.lon,
                    "ground_speed": self.ground_speed,
                    "air_speed": self.air_speed,
                    "battery": self.battery,
                    "waypoint": self.waypoint,
                    "dist_from_home": self.dist_to_home,
                    "connection": self.connection,
                }
            }
        except Exception as e:
            raise GeneralError(str(e)) from e

    def stats(self):
        return {
            "result": {
                "quick": self.quick()["result"],
                "mode": self.mode.name,
                "armed": self.get_armed()["result"],
                "status": self.vehicle.system_status.state,
            }
        }

    # Flight Mode

    def get_flight_mode(self):
        try:
            self.mode = self.vehicle.mode
            return {"result": self.mode.name}
        except Exception as e:
            raise GeneralError(str(e)) from e

    # Armed

    def get_armed(self):
        try:
            if self.vehicle.armed:
                return {"result": "ARMED"}
            elif self.vehicle.is_armable:
                return {"result": "DISARMED (ARMABLE)"}
            else:
                return {"result": "DISARMED (NOT ARMABLE)"}
        except Exception as e:
            raise GeneralError(str(e)) from e

    def arm(self):
        try:
            if not self.vehicle.is_armable:
                self.logger.important("Vehicle is not armable")
            self.vehicle.arm(wait=True, timeout=15)  # Motors can be started
            return {}
        except TimeoutError as e:
            raise TimeoutError("Vehicle arming timed out") from e
        except InvalidStateError as e:
            raise InvalidStateError(str(e)) from e
        except Exception as e:
            # raise InvalidStateError("Vehicle is not armable")
            raise GeneralError(str(e)) from e

    def disarm(self):
        try:
            self.vehicle.disarm(wait=True, timeout=15)
            return {}
        except TimeoutError as e:
            raise TimeoutError("Vehicle disarming timed out") from e
        except Exception as e:
            raise GeneralError(str(e)) from e

    def __repr__(self):
        return "UAV Handler"
