import socket
import json
import threading
from collections import deque
import cv2

def setup():
    global config, queue
    config = json.load("config.json")
    queue = deque([])
    connect_gcs()
    recv_thread = threading.Thread(target=recv)
    recv_thread.daemon = True
    recv_thread.start()
    send_thread = threading.Thread(target=send)
    send_thread.daemon = True
    send_thread.start()

def connect_gcs():
    global config, sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((config["GS_IP"], config["GS_PORT"]))

def recv():
    global sock
    while True:
        data = sock.recv(config["GS_BUFFER"])

def send():
    global queue
    while True:
        if queue:
            sock.send(queue.popleft())

def send_img(img):
    global queue
    data = cv2.imencode('.jpg', img)[1].tostring()
    queue.append(data)