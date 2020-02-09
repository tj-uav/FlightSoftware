from time import sleep
import signal, os, subprocess

import cv2
import io
import socket
import struct
import time
import pickle
import zlib
from PIL import Image
def cv2encode(img):
    _, encoded = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
#    return encoded
    return pickle.dumps(encoded)
    #return pickle.dumps(img)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.1.106', 8485))
# connection = client_socket.makefile('wb')

# cam.set(3, 960)
# cam.set(4, 720)

img_counter = 0

i = 0
start_time = time.time()
#while True:
for i in range(2):
    os.system('gphoto2 --capture-image-and-download --keep --force-overwrite --filename=/home/tjuav/flight_pics/'+str(i))
    filename = '/home/tjuav/flight_pics/'+str(i)
    i += 1
#    pil_img = Image.open(filename)
#    pil_img.save(filename+'.jpg', quality=30)
    frame = cv2.imread(filename)
    print(frame.shape)
#    data = zlib.compress(pickle.dumps(frame, 0))
    data = cv2encode(frame)
    print(type(data))

    size = len(data)
    print('size',size)

    print("{}: {}".format(img_counter, size))
    client_socket.sendall(struct.pack(">L", size) + data)

    print(i)
    print((time.time() - start_time) / i)

client_socket.close()
#cam.release()
