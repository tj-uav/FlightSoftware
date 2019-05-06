import cv2
import time

def get_frame():
    ret, frame = cap.read()
    if ret==True:
        frame = cv2.flip(frame,0)
        frame = cv2.flip(frame, 1)

    return ret,frame

cap = cv2.VideoCapture(0)

while(cap.isOpened()):
    ret,frame = get_frame()
    cv2.imshow("Frame",frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): # End video feed when 'q' is pressed
        break


cap.release()