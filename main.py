import json
import os.path
import sys

from flask import Flask, send_file
import threading
import cv2 as cv
import datetime

with open("config.json", "r") as file:
    config = json.load(file)


app = Flask(__name__)

last_image: int = -1
lock = threading.Lock()


def log(text: str):
    print(str(datetime.datetime.now()) + " | " + text)
    with open("fs.log", "a", encoding="utf-8") as file:
        file.write(str(datetime.datetime.now()) + " | " + text + "\n")


def stop():
    if os.path.getsize("stop.txt") > 0:
        return True
    return False


def take_image(cam: cv.VideoCapture):
    if stop():
        log("Detected content in \"stop.txt\" file. Images will no longer be taken.")
        sys.exit()
    with lock:
        threading.Timer(2.0, take_image, [cam]).start()
        ret, frame = cam.read()
        if not ret:
            return False
        log("Captured frame")
        global last_image
        last_image += 1
        img_quality = config["image"]["quality"]
        if img_quality == -1:
            cv.imwrite(f"assets/images/{last_image}.png", frame)
        else:
            cv.imwrite(
                f"assets/images/{last_image}.jpg", frame, [int(cv.IMWRITE_JPEG_QUALITY), img_quality]
            )
        log("Saved image " + str(last_image))
        return True


def take_dummy_image():
    if stop():
        log("Detected content in \"stop.txt\" file. Images will no longer be taken.")
        sys.exit()
    with lock:
        threading.Timer(2.0, take_dummy_image).start()
        global last_image
        last_image += 1
        cv.imwrite(f"assets/images/{last_image}.png", cv.imread("sample.png"))
        cv.imwrite(
            f"assets/images/{last_image}.jpg",
            cv.imread("sample.png"),
            [int(cv.IMWRITE_JPEG_QUALITY), config["image"]["quality"]],
        )
        return True


def take_images():
    cam = cv.VideoCapture(config["image"]["device"])
    cam.set(cv.CAP_PROP_FRAME_WIDTH, config["image"]["width"])
    cam.set(cv.CAP_PROP_FRAME_HEIGHT, config["image"]["height"])
    if config["image"]["dummy"]:
        take_dummy_image()
    else:
        take_image(cam)


@app.route("/")
def index():
    return "Hello from Avalon!"


@app.route("/last_image")
def get_last_image():
    return {"result": last_image}


@app.route("/image/<int:image_id>")
def image(image_id):
    if image_id > last_image:
        return {"result": "Image not found"}
    filename = f"assets/images/{image_id}.jpg" if config["image"]["quality"] > 0 else f"assets/images/{image_id}.png"
    return send_file(filename, mimetype="image/png")


def run_server():
    app.run()  #host="0.0.0.0", port=4000, debug=True)


if __name__ == "__main__":
    webserver = threading.Thread(target=run_server)
    webserver.start()
    take_images()
