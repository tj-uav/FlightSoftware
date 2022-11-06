import json
import os
import sys
import subprocess

from flask import Flask, send_file
import threading
import cv2 as cv
import gphoto2 as gp
import datetime, time

FILEPATH = "/home/tjuav/FlightSoftware"
IMAGE_INTERVAL = 0.5 # Image interval in seconds

with open(FILEPATH + "/config.json", "r") as file:
    config = json.load(file)

app = Flask(__name__)

lock = threading.Lock()


def log(text: str):
    print(str(datetime.datetime.now()) + " | " + text)
    with open(FILEPATH + "/fs.log", "a", encoding="utf-8") as file:
        file.write(str(datetime.datetime.now()) + " | " + text + "\n")


def stop():
    if os.path.getsize(FILEPATH + "/stop.txt") > 0:
        return True
    return False


def get_img_cnt() -> int:
    with open(FILEPATH + "/img_cnt.txt", "r", encoding="utf-8") as file:
        return int(file.read())


def set_img_cnt(cnt: int):
    with open(FILEPATH + "/img_cnt.txt", "w", encoding="utf-8") as file:
        file.write(str(cnt))

# https://github.com/jdemaeyer/ice/blob/master/ice/__init__.py
def set_config(camera, context, config_name, value):
    log("Setting '{}' to '{}'".format(config_name, value))
    config = gp.check_result(
                gp.gp_camera_get_config(camera, context))
    widget = gp.check_result(
                gp.gp_widget_get_child_by_name(config, config_name))
    gp.check_result(gp.gp_widget_set_value(widget, value))
    gp.check_result(
            gp.gp_camera_set_config(camera, config, context))
    log("Set '{}' to '{}'".format(config_name, value))

def take_image():
    log('Please connect and switch on the camera')
    camera = gp.Camera()
    while True:
        error = gp.gp_camera_init(camera)
        if error >= gp.GP_OK:
            # operation completed successfully so exit loop
            log("Camera Connected")
            break
        if error != gp.GP_ERROR_MODEL_NOT_FOUND:
            # some other error we can't handle here
            raise gp.GPhoto2Error(error)
        log("No Camera Found, trying again")
        time.sleep(1)
    context = gp.gp_context_new()
    set_config(camera, context, "f-number", config["image"]["f-number"])
    set_config(camera, context, "iso", config["image"]["iso"])
    set_config(camera, context, "shutterspeed", config["image"]["shutterspeed"])
    captime = time.perf_counter()
    while True:
        if stop():
            log('Detected content in "stop.txt" file. Images will no longer be taken.')
            sys.exit()
        with lock:
            last_image = get_img_cnt()
            set_img_cnt(last_image + 1)
            if time.perf_counter() - captime > IMAGE_INTERVAL:
                camera.trigger_capture()
                captime = time.perf_counter()
            event_type, event_data = camera.wait_for_event(1000)
            if event_type == gp.GP_EVENT_FILE_ADDED:
                cam_file = camera.file_get(
                    event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                target_path = f"{FILEPATH}/assets/images/{last_image + 1}.png"
                log("Image is being saved to {}".format(target_path))
            cam_file.save(target_path)


def take_dummy_image():
    if stop():
        log('Detected content in "stop.txt" file. Images will no longer be taken.')
        sys.exit()
    with lock:
        threading.Timer(2.0, take_dummy_image).start()
        last_image = get_img_cnt()
        set_img_cnt(last_image + 1)
        img = cv.imread(FILEPATH + "/assets/images/sample.png")
        cv.imwrite(f"{FILEPATH}/assets/images/{last_image + 1}.png", img)


def take_images():
    if config["image"]["dummy"]:
        take_dummy_image()
    else:
        threading.Thread(target = take_image).start()


@app.route("/")
def index():
    return "Hello from Avalon!"


@app.route("/last_image")
def get_last_image():
    return {"result": get_img_cnt()}


@app.route("/image/<int:image_id>")
def image(image_id):
    if image_id > get_img_cnt():
        return {"result": "Image not found"}
    filename = f"{FILEPATH}/assets/images/{image_id}.png"
    return send_file(filename, mimetype="image/png")


if __name__ == "__main__":
    set_img_cnt(-1)
    take_images()
    app.run(host="0.0.0.0", port=4000, debug=True, threaded=True)
