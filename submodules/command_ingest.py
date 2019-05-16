import logging
import cv2
import time
from submodules import telemetry 

logger = logging.getLogger("CI")
cap = cv2.VideoCapture(0)

def ingest_message():
    """
    Sends message to respective method based on header
    """
    logger.debug("Ingesting message")
    pass


def send_image():
    while(cap.isOpened()):
        ret,frame = get_frame()
        rgbFrame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        frame_str = cv2.imencode('.jpg', rgbFrame)[1].tostring()
        telemetry.enqueue(frame_str)


def get_frame():
    ret, frame = cap.read()
    if ret==True:
        frame = cv2.flip(frame,0)
        frame = cv2.flip(frame, 1)

    return ret,frame


cap.release()