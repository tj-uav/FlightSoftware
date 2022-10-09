import json
import os
import sys
import subprocess

from flask import Flask, send_file
import threading
import cv2 as cv
import datetime

IMAGE_COMMAND = ["gphoto2", "--capture-image-and-download", "--force-overwrite", "--filename"]

with open("config.json", "r") as file:
    config = json.load(file)


app = Flask(__name__)

lock = threading.Lock()


def log(text: str):
    print(str(datetime.datetime.now()) + " | " + text)
    with open("fs.log", "a", encoding="utf-8") as file:
        file.write(str(datetime.datetime.now()) + " | " + text + "\n")


def stop():
    if os.path.getsize("stop.txt") > 0:
        return True
    return False


def get_img_cnt() -> int:
    with open("img_cnt.txt", "r", encoding="utf-8") as file:
        return int(file.read())


def set_img_cnt(cnt: int):
    with open("img_cnt.txt", "w", encoding="utf-8") as file:
        file.write(str(cnt))


def take_image():
    if stop():
        log('Detected content in "stop.txt" file. Images will no longer be taken.')
        sys.exit()
    with lock:
        threading.Timer(5.0, take_image).start()
        last_image = get_img_cnt()
        set_img_cnt(last_image)
        subprocess.Popen(IMAGE_COMMAND + [f"assets/images/{last_image + 1}.png"])


def take_dummy_image():
    if stop():
        log('Detected content in "stop.txt" file. Images will no longer be taken.')
        sys.exit()
    with lock:
        threading.Timer(5.0, take_dummy_image).start()
        last_image = get_img_cnt()
        set_img_cnt(last_image)
        img = cv.imread("assets/images/sample.png")
        cv.imwrite(f"assets/images/{last_image + 1}.png", img)


def take_images():
    if config["image"]["dummy"]:
        take_dummy_image()
    else:
        take_image()


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
    filename = f"assets/images/{image_id}.png"
    return send_file(filename, mimetype="image/png")


if __name__ == "__main__":
    set_img_cnt(-1)
    take_images()
    app.run(host="0.0.0.0", port=4000, debug=True, threaded=True)
