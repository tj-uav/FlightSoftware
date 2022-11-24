import json
import os
import sys

from flask import Flask, send_file, request
import threading
import cv2 as cv
import gphoto2 as gp
import datetime
import time

from uav import UAVHandler

IMAGE_INTERVAL = 0.5  # Image interval in seconds

with open(os.path.join(os.getcwd(), "config.json"), "r", encoding="utf-8") as file:
    config = json.load(file)

app = Flask(__name__)

uav_handler = UAVHandler(config)
uav_handler.connect()
uav_lock = threading.Lock()

paused = True
paused_lock = threading.Lock()

stopped = False
stopped_lock = threading.Lock()

img_count = -1
image_data = {}
img_lock = threading.Lock()


def log(text: str) -> None:
    print(str(datetime.datetime.now()) + " | " + text)
    with open(os.path.join(os.getcwd(), "fs.log"), "a", encoding="utf-8") as file:
        file.write(str(datetime.datetime.now()) + " | " + text + "\n")


def change_setting(camera, context):
    """
    Checks if config json has changed, and if so updates config and sets new settings
    """
    global config
    with open(os.path.join(os.getcwd(), "config.json"), "r") as file:
        new_config = json.load(file)

    if config["image"]["f-number"] != new_config["image"]["f-number"] or config["image"]["iso"] != new_config["image"]["iso"] or config["image"]["shutterspeed"] != new_config["image"]["shutterspeed"]:
        config = new_config
        set_config(camera, context, "f-number", config["image"]["f-number"])
        time.sleep(3)
        set_config(camera, context, "iso", config["image"]["iso"])
        time.sleep(3)
        set_config(camera, context, "shutterspeed", config["image"]["shutterspeed"])
        time.sleep(3)


# https://github.com/jdemaeyer/ice/blob/master/ice/__init__.py
def set_config(camera, context, config_name, value):
    """
    Change a setting on the camera
    """
    log("Setting '{}' to '{}'".format(config_name, value))
    current_config = gp.check_result(gp.gp_camera_get_config(camera, context))
    widget = gp.check_result(gp.gp_widget_get_child_by_name(current_config, config_name))
    gp.check_result(gp.gp_widget_set_value(widget, value))
    gp.check_result(gp.gp_camera_set_config(camera, current_config, context))
    log("Set '{}' to '{}'".format(config_name, value))


def take_image():
    log("Please connect and switch on the camera")
    error, camera = gp.gp_camera_new()
    while True:  # Wait for camera to be connected
        error = gp.gp_camera_init(camera, None)
        if error >= gp.GP_OK:
            # operation completed successfully so exit loop
            log("Camera Connected")
            break
        if error != gp.GP_ERROR_MODEL_NOT_FOUND:
            # some other error we can't handle here
            raise gp.GPhoto2Error(error)
        with stopped_lock:
            if stopped:
                log("Image-taking has been stopped.")
                camera.exit()
                sys.exit()
        log("No Camera Found, trying again")
        time.sleep(2)
    # Log the detected camera
    error, text = gp.gp_camera_get_summary(camera, None)
    log(text.text)

    context = gp.gp_context_new()
    # Set aperture, iso, shutterspeed
    # The camera takes some time to "ramp up" to the setting instead of instantly setting the setting, so we wait 3 seconds between each setting change
    time.sleep(3)
    set_config(camera, context, "f-number", config["image"]["f-number"])
    time.sleep(3)
    set_config(camera, context, "iso", config["image"]["iso"])
    time.sleep(3)
    set_config(camera, context, "shutterspeed", config["image"]["shutterspeed"])

    captime = time.time()
    while True:
        with stopped_lock:
            if stopped:
                log("Image-taking has been stopped.")
                camera.exit()
                sys.exit()

        # Change settings if needed
        change_setting(camera, context)

        # Capture image every image interval, unless told to wait
        with paused_lock:
            if paused or time.time() - captime < IMAGE_INTERVAL:
                time.sleep(0.1)
                continue
            else:
                with uav_lock:
                    uav_loc = uav_handler.location()
                lat1, lon1, alt1, altg1 = uav_loc["lat"], uav_loc["lon"], uav_loc["alt"], uav_loc["altg"]
                camera.trigger_capture()
                log("Image captured")
                captime = time.time()

        # Wait for new image to appear, and download and save that image directly from camera
        event_type, event_data = camera.wait_for_event(1000)
        if event_type == gp.GP_EVENT_FILE_ADDED:
            with uav_lock:
                uav_loc = uav_handler.location()
            lat2, lon2, alt2, altg2 = uav_loc["lat"], uav_loc["lon"], uav_loc["alt"], uav_loc["altg"]
            current_image_data = [(lat1 + lat2) / 2, (lon1 + lon2) / 2, (alt1 + alt2) / 2, (altg1 + altg2) / 2]
            with img_lock:
                global img_count
                img_count += 1
                image_data[img_count] = current_image_data
                cam_file = camera.file_get(
                    event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                target_path = os.path.join(os.getcwd(), "assets", "images", f"{img_count}.png")
                log(f"Image is being saved to {target_path}")
                cam_file.save(target_path)


def take_dummy_image():
    captime = time.time()
    while True:
        with stopped_lock:
            if stopped:
                log("Image-taking has been stopped.")
                sys.exit()
        with paused_lock:
            if time.time() - captime > IMAGE_INTERVAL and not paused:
                with uav_lock:
                    uav_loc = uav_handler.location()
                lat, lon, alt, altg = uav_loc["lat"], uav_loc["lon"], uav_loc["alt"], uav_loc["altg"]
                current_image_data = [lat, lon, alt, altg]
                with img_lock:
                    global img_count
                    img_count += 1
                    image_data[img_count] = current_image_data
                    img = cv.imread(os.path.join(os.getcwd(), "assets", "images", "sample.png"))
                    target_path = os.path.join(os.getcwd(), "assets", "images", f"{img_count}.png")
                    cv.imwrite(target_path, img)
                    log(f"Dummy image saved to {target_path}")
                    captime = time.time()
            else:
                time.sleep(0.1)
                continue


def update_uav():
    while True:
        with stopped_lock:
            if stopped:
                log("UAV update has been stopped.")
                uav_handler.vehicle.close()
                sys.exit()
        with uav_lock:
            uav_handler.update()
        time.sleep(0.1)


@app.route("/")
def index():
    return "Hello from Avalon!"


@app.route("/last_image")
def get_last_image():
    with img_lock:
        return {"result": img_count}


@app.route("/image_data")
def get_image_data():
    with img_lock:
        return {"result": image_data}


@app.route("/image/<int:image_id>")
def image(image_id):
    with img_lock:
        if image_id > img_count:
            return {"result": "Image not found"}
    filename = os.path.join(os.getcwd(), "assets", "images", f"{image_id}.png")
    return send_file(filename, mimetype="image/png")


@app.route("/pause", methods=["POST"])
def pause():
    with paused_lock:
        global paused
        paused = True
    return {}


@app.route("/resume", methods=["POST"])
def resume():
    with paused_lock:
        global paused
        paused = False
    return {}


# Also uses the GET method for emergency stop from browser
@app.route("/stop", methods=["GET", "POST"])
def stop():
    with stopped_lock:
        global stopped
        stopped = True
    return {}


@app.teardown_request
def stop_app(_):
    is_stopped = None
    with stopped_lock:
        is_stopped = stopped
    if is_stopped:
        time.sleep(10)
        os._exit(0)


if __name__ == "__main__":
    image_thread = threading.Thread(target=take_dummy_image if config["image"]["dummy"] else take_image)
    uav_update_thread = threading.Thread(target=update_uav)
    image_thread.start()
    uav_update_thread.start()

    app.run(host="0.0.0.0", port=4000, threaded=True)
