import json
import os
import sys

from flask import Flask, send_file
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

image_data = {}

uav_handler = UAVHandler(config)
uav_handler.connect()
uav_lock = threading.Lock()


def log(text: str) -> None:
    print(str(datetime.datetime.now()) + " | " + text)
    with open(os.path.join(os.getcwd(), "fs.log"), "a", encoding="utf-8") as file:
        file.write(str(datetime.datetime.now()) + " | " + text + "\n")


def stop() -> bool:
    """
    Checks if stop.txt has any contents, and if so stops the script
    """
    if os.path.getsize(os.path.join(os.getcwd(), "stop.txt")) > 0:
        return True
    return False


def wait() -> bool:
    """
    Checks if wait.txt has any contents, and if so, does not take images but continues to run the script
    """
    if os.path.getsize(os.path.join(os.getcwd(), "wait.txt")) > 0:
        return True
    return False


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


def get_img_cnt() -> int:
    with open(os.path.join(os.getcwd(), "img_cnt.txt"), "r", encoding="utf-8") as file:
        return int(file.read())


def set_img_cnt(cnt: int):
    with open(os.path.join(os.getcwd(), "img_cnt.txt"), "w", encoding="utf-8") as file:
        file.write(str(cnt))


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
        if stop():
            log('Detected content in "stop.txt" file. Images will no longer be taken.')
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
        if stop():
            log('Detected content in "stop.txt" file. Images will no longer be taken.')
            camera.exit()
            sys.exit()

        # Change settings if needed
        change_setting(camera, context)

        # Capture image every image interval, unless told to wait
        if time.time() - captime > IMAGE_INTERVAL and not wait():
            with uav_lock:
                uav_loc = uav_handler.location()
            lat1, lon1, alt1, altg1 = uav_loc["lat"], uav_loc["lon"], uav_loc["alt"], uav_loc["altg"]
            camera.trigger_capture()
            log("Image captured")
            captime = time.time()
        else:
            time.sleep(0.1)
            continue

        # Wait for new image to appear, and download and save that image directly from camera
        event_type, event_data = camera.wait_for_event(1000)
        if event_type == gp.GP_EVENT_FILE_ADDED:
            with uav_lock:
                uav_loc = uav_handler.location()
            lat2, lon2, alt2, altg2 = uav_loc["lat"], uav_loc["lon"], uav_loc["alt"], uav_loc["altg"]
            current_image_data = [(lat1 + lat2) / 2, (lon1 + lon2) / 2, (alt1 + alt2) / 2, (altg1 + altg2) / 2]
            last_image = get_img_cnt() + 1
            set_img_cnt(last_image)
            image_data[last_image] = current_image_data
            cam_file = camera.file_get(
                event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
            target_path = os.path.join(os.getcwd(), "assets", "images", f"{last_image}.png")
            log(f"Image is being saved to {target_path}")
            cam_file.save(target_path)


def take_dummy_image():
    captime = time.time()
    while True:
        if stop():
            log('Detected content in "stop.txt" file. Images will no longer be taken.')
            sys.exit()
        if time.time() - captime > IMAGE_INTERVAL and not wait():
            last_image = get_img_cnt()
            set_img_cnt(last_image + 1)
            img = cv.imread(os.path.join(os.getcwd(), "assets", "images", "sample.png"))
            cv.imwrite(os.path.join(os.getcwd(), "assets", "images", f"{last_image + 1}.png"), img)
            log(f"Dummy image saved to {os.path.join(os.getcwd(), 'assets', 'images', f'{last_image + 1}.png')}")
            captime = time.time()
        else:
            time.sleep(0.1)
            continue


def update_uav():
    while True:
        if stop():
            log('Detected content in "stop.txt" file. GPS data will no longer be collected.')
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
    return {"result": get_img_cnt()}


@app.route("/image_data")
def get_image_data():
    return {"result": image_data}


@app.route("/image/<int:image_id>")
def image(image_id):
    if image_id > get_img_cnt():
        return {"result": "Image not found"}
    filename = os.path.join(os.getcwd(), "assets", "images", f"{image_id}.png")
    return send_file(filename, mimetype="image/png")


if __name__ == "__main__":
    set_img_cnt(-1)

    image_thread = threading.Thread(target=take_dummy_image if config["image"]["dummy"] else take_image)
    uav_update_thread = threading.Thread(target=update_uav)
    image_thread.start()
    uav_update_thread.start()

    app.run(host="0.0.0.0", port=4000, threaded=True)
