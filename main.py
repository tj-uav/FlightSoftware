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

IMAGE_INTERVAL = 0.75  # Image interval in seconds

with open(os.path.join(os.getcwd(), "config.json"), "r", encoding="utf-8") as file:
    config = json.load(file)

app = Flask(__name__)

uav_handler = UAVHandler(config)
uav_handler.connect()
uav_lock = threading.Lock()

paused = True
paused_by_script = False
paused_lock = threading.Lock()

stopped = False
stopped_lock = threading.Lock()

img_count = -1
image_data = {}
img_lock = threading.Lock()

current_config = {"f-number": None, "iso": None, "shutterspeed": None, "exposurecompensation": None}
new_config = None
config_lock = threading.Lock()


def log(text: str) -> None:
    print(str(datetime.datetime.now()) + " | " + text)
    with open(os.path.join(os.getcwd(), "fs.log"), "a", encoding="utf-8") as file:
        file.write(str(datetime.datetime.now()) + " | " + text + "\n")


def change_settings(camera, context, f_number=None, iso=None, shutterspeed=None, exposurecompensation=None):
    # The camera takes some time to "ramp up" to the setting instead of instantly setting the setting, so we wait 3 seconds between each setting change
    global paused_by_script
    with paused_lock:
        paused_by_script = True
    with config_lock:
        if f_number is not None and f_number != current_config["f-number"]:
            set_config(camera, context, "f-number", f_number)
            time.sleep(3)
            current_config["f-number"] = f_number
        if iso is not None and iso != current_config["iso"]:
            set_config(camera, context, "iso", iso)
            time.sleep(3)
            current_config["iso"] = iso
        if shutterspeed is not None and shutterspeed != current_config["shutterspeed"]:
            set_config(camera, context, "shutterspeed", shutterspeed)
            time.sleep(3)
            current_config["shutterspeed"] = shutterspeed
        if exposurecompensation is not None and exposurecompensation != current_config["exposurecompensation"]:
            set_config(camera, context, "exposurecompensation", exposurecompensation)
            time.sleep(3)
            current_config["exposurecompensation"] = exposurecompensation
    with paused_lock:
        paused_by_script = False


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
        log("No Camera Found, trying again")
        time.sleep(2)
    # Log the detected camera
    error, text = gp.gp_camera_get_summary(camera, None)
    log(text.text)

    # Set aperture, iso, shutterspeed
    context = gp.gp_context_new()
    change_settings(
        camera,
        context,
        None,  # config["image"]["f-number"],
        config["image"]["iso"],
        None,  # config["image"]["shutterspeed"],
        config["image"]["exposurecompensation"]
    )

    captime = time.time()
    while True:
        with stopped_lock:
            if stopped:
                log("Image-taking has been stopped.")
                camera.exit()

        # Change settings if needed
        do_change = False
        with config_lock:
            global new_config
            if new_config is not None:
                do_change = True
                f_number = new_config["f-number"]
                iso = new_config["iso"]
                shutterspeed = new_config["shutterspeed"]
                exposurecompensation = new_config["exposurecompensation"]
        if do_change:
            change_settings(camera, context, f_number, iso, shutterspeed, exposurecompensation)
            new_config = None

        # Capture image every image interval, unless told to wait
        with paused_lock:
            is_paused = paused
            is_paused_by_script = paused_by_script
        if is_paused or is_paused_by_script:
            log(f"Paused: {is_paused=} {is_paused_by_script=}")
            time.sleep(0.5)
            continue
        elif time.time() - captime < IMAGE_INTERVAL:
            time.sleep(0.1)
            continue
        else:
            with uav_lock:
                uav_loc = uav_handler.location()
            lat, lon, alt, altg, heading = (
                uav_loc["lat"],
                uav_loc["lon"],
                uav_loc["alt"],
                uav_loc["altg"],
                uav_loc["heading"],
            )
            with config_lock:
                f_number, iso, shutterspeed, exposurecompensation = (
                    current_config["f-number"],
                    current_config["iso"],
                    current_config["shutterspeed"],
                    current_config["exposurecompensation"],
                )
            camera.trigger_capture()
            log("Image capture sent")
            captime = time.time()

        # Wait for new image to appear, and download and save that image directly from camera
        event_type, event_data = camera.wait_for_event(1000)
        while event_type != gp.GP_EVENT_FILE_ADDED:
            log(f"Code {event_type}: {event_data}")
            with stopped_lock:
                if stopped:
                    log("Image-taking has been stopped.")
                    camera.exit()
                    return
            event_type, event_data = camera.wait_for_event(1000)
        log("Image file path retrieved")
        current_image_data = {
            "lat": lat,
            "lon": lon,
            "alt": alt,
            "altg": altg,
            "heading": heading,
            "f-number": f_number,
            "iso": iso,
            "shutterspeed": shutterspeed,
            "exposurecompensation": exposurecompensation,
        }
        with img_lock:
            global img_count
            img_count += 1
            image_data[img_count] = current_image_data
            cam_file = camera.file_get(
                event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL
            )
            target_path = os.path.join(os.getcwd(), "assets", "images", f"{img_count}.png")
            if img_count % 20 == 0:
                log(f"Image data is being saved to image_data.json (image {img_count})")
                with open("image_data.json", "w") as file:
                    json.dump(image_data, file, indent=4)
        log(f"Image is being saved to {target_path}")
        cam_file.save(target_path)


def take_dummy_image():
    captime = time.time()
    while True:
        with stopped_lock:
            if stopped:
                log("Image-taking has been stopped.")
        with paused_lock:
            is_paused = paused
            is_paused_by_script = paused_by_script
        if is_paused or is_paused_by_script:
            log(f"Paused: {is_paused=} {is_paused_by_script=}")
            time.sleep(0.5)
            continue
        elif time.time() - captime < IMAGE_INTERVAL:
            time.sleep(0.1)
            continue
        else:
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


def update_uav():
    while True:
        with stopped_lock:
            if stopped:
                log("UAV update has been stopped.")
                uav_handler.vehicle.close()
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


@app.route("/image_data/<int:image_id>")
def get_image_data_by_id(image_id):
    with img_lock:
        if image_id <= img_count:
            return {"result": image_data[image_id]}
    return {"result": "Image not found"}


@app.route("/image/<int:image_id>")
def image(image_id):
    with img_lock:
        if image_id > img_count:
            return {"result": "Image not found"}
    filename = os.path.join(os.getcwd(), "assets", "images", f"{image_id}.png")
    return send_file(filename, mimetype="image/png")


@app.route("/config")
def get_camera_config():
    with config_lock:
        return {"result": current_config}


@app.route("/setconfig", methods=["POST"])
def set_camera_config():
    f = request.json
    with config_lock:
        global new_config
        new_config = {
            "f-number": f.get("f-number"),
            "iso": f.get("iso"),
            "shutterspeed": f.get("shutterspeed"),
            "exposurecompensation": f.get("exposurecompensation"),
        }
    with paused_lock:
        global paused_by_script
        paused_by_script = True
    return {}


@app.route("/status")
def status():
    with paused_lock, stopped_lock:
        return {
            "result": {"paused": paused, "paused_by_script": paused_by_script, "stopped": stopped}
        }


@app.route("/pause", methods=["GET", "POST"])
def pause():
    with paused_lock:
        global paused
        paused = True
    log("Image data is being saved to image_data.json (since image taking has been paused)")
    with open("image_data.json", "w") as file:
        json.dump(image_data, file, indent=4)
    return {}


@app.route("/resume", methods=["GET", "POST"])
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
    log("Image data is being saved to image_data.json (since image taking has been stopped)")
    with open("image_data.json", "w") as file:
        json.dump(image_data, file, indent=4)
    with open(f"image_data_{time.time()}.json", "w") as file:
        json.dump(image_data, file, indent=4)
    return {}


@app.teardown_request
def stop_app(_):
    is_stopped = None
    with stopped_lock:
        is_stopped = stopped
    if is_stopped:
        time.sleep(10)
        sys.exit(5)


if __name__ == "__main__":
    image_thread = threading.Thread(
        target=take_dummy_image if config["image"]["dummy"] else take_image
    )
    uav_update_thread = threading.Thread(target=update_uav)
    image_thread.start()
    uav_update_thread.start()

    app.run(host="0.0.0.0", port=4000, threaded=True)
