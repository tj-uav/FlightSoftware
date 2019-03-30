import cv2
import keras
from keras.datasets import mnist
from keras.models import Sequential, model_from_json
from keras.layers import *
from keras.optimizers import *
import numpy as np
from tqdm import tqdm
import cv2
from random import shuffle
import os
import matplotlib.pyplot as plt
from core import config

#List of objects currently being detected
active_objects = []

def start():
    global rgbcolor_dict
    rgbcolor_dict = {}
    filename = config['detection']['rgb_filename']
    try:
        file = open(filename,"r")
        lines = file.readlines()
        for line in lines:
            rgb,color = line.split(" ")
            rgb = rgb[1:len(rgb)-1]
            rgbcolor_dict[rgb] = color
    except:
        logger.debug("File not found")

    #Initialize neural networks, haar cascade, other stuff
    pass

def haar_cascade(image):
    #If ROI detected:
    t = ThreadHandler(target=partial(process_image), args=[image,object_image]
                       name="detection-process_image")
    t.start()
    pass

def process_image(original_img, object_img):
    """
    This method is called when the haar cascade detects an ROI suspicious of being an object
    """
    shape,shape_range = classify_shape(object_img, shape_color)
    alpha,alpha_range = classify_alpha(object_img, alpha_color)
    (obj_latitude,obj_longitude) = get_position()
    shape_color = get_alpha_color(shape_range)
    alpha_color = get_shape_color(shape_range,alpha_range)
    dict = {"shape":shape, "alpha":alpha, "latitude":latitude, "longitude":longitude}
    send_json(dict)

#Classify color based on pixel range
#Ignore pixels in the ignore_range
#Range of pixels is given by array of [x,y] values
def get_color(image,main_range,ignore_range = None):
    global rgbcolor_dict
    colorlist = {}
    new_range = []
    if ignore_range is None:
        ignore_range = []
    else:

    for [x,y] in range():
        for rgb_value in row:
            [r,g,b] = rgb_value
            color = rgbcolor_dict[rgb_value]
            if color in colorlist:
                colorlist[color] += 1
            else:
                colorlist[color] = 1
    return max(colorlist)

#Classify the shape using tensorflow neural network
def classify_shape(object_img, color):
    pass

#Classify the alphanumeric using tensorflow neural network
def classify_alpha(object_img, color):
    pass

#Return current gps data of the plane
def get_gps_data():
    pass

def get_camera_angle():
    pass

def get_position(image, center):
    gps_data = get_gps_data()
    plane_altitude = gps_data["altitude"]
    plane_latitude = gps_data["latitude"]
    plane_longitude = gps_data["longitude"]
    camera_angle = get_camera_angle()
    #Do some quick maths
    return (object_latitude, object_longitude)

def send_json(info):
    pass
