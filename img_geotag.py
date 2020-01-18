# from auvsi_suas.client import client
# from auvsi_suas.proto import interop_api_pb2
# from google.protobuf import json_format

import socket
import sys
import cv2
import pickle
import numpy as np
import struct
import time


def create_blank():
    odlc = interop_api_pb2.Odlc()
    print(odlc)
    odlc.mission = 1
    odlc.type = interop_api_pb2.Odlc.STANDARD
    odlc.latitude = 50
    odlc.longitude = 50
    odlc.orientation = 1
    odlc.shape = 1
    odlc.shape_color = 1
    odlc.alphanumeric = 'A'
    odlc.alphanumeric_color = 1
    return odlc

if __name__ == "__main__":
    # cl = client.AsyncClient(url="http://192.168.1.108:8000", username="testuser", password="testpass")
    file = open("output.txt", "w+")
    oldtime = time.perf_counter()
    HOST=''
    PORT=8485
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    print('Socket created')
    num=0
    s.bind((HOST,PORT))
    print('Socket bind complete')
    s.listen(1)
    print('Socket now listening')

    conn,addr=s.accept()

    data = b""
    payload_size = struct.calcsize(">L")
    print("payload_size: {}".format(payload_size))
    file.write('Time\tFPS')
    t0 = time.time()
    while True:
        while len(data) < payload_size:
            #print("Recv: {}".format(len(data)))
            data += conn.recv(4096)

        #print("Done Recv: {}".format(len(data)))
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]
        #print("msg_size: {}".format(msg_size))
        while len(data) < msg_size:
            data += conn.recv(4096)
        frame_data = data[:msg_size]
        data = data[msg_size:]


        frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        # cv2.imwrite('C:/Users/ganes/Pictures/flight_pics/image_'+str(8800+num)+'.jpg',frame)
        cv2.imwrite('E:/Jason/UAV/flight_pics/image_'+str(8800+num)+'.jpg',frame)
        if num % 200 == 0:
            f = open('E:/Jason/UAV/flight_pics/image_'+str(8800+num)+'.jpg', 'rb')
            odlc = create_blank()
            odlc_object = cl.post_odlc(odlc).result()
            cl.put_odlc_image(odlc_object.id, f.read())
            f.close()
    #  cv2.imshow("img", frame)
    #  cv2.waitKey(1)

        num=num+1
        if (time.time()-t0)>5:
            f.write('{}\t{}'.format(round(time.time(),3), round((num-oldNum)/5),3))
            oldNum = num
            t0 = time.time()

        #print("num: "+ str(num) + ", time: " + str(round(time.time()-oldtime,4)) + ", avg. speed: " + str(round(num/(time.time()-oldtime), 4)) + " fps")