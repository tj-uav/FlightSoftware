import cv2
import keras
from keras.datasets import mnist
from keras.models import model_from_json
import numpy as np
import cv2
from core import config
from helpers.threadhandler import ThreadHandler
from functools import partial

#List of objects currently being detected
active_objects = []
cascades = {} #Cascade for each shape
shapes = ["triangle"]
alphaNetwork = None
shapeNetwork = None
bufferFraction = 0.25
colors_dict = {}

def start():
    for shape in shapes:
        cascade = cv2.CascadeClassifier("xml_files/"+shape+"_cascade.xml")
        cascades[shape] = cascade

    colors_dict = load_colors(config['detection']['colors_filename'])
    alphaNetwork = load_model(config['detection']['alphanumeric_model_name'])
    shapeNetwork = load_model(config['detection']['shape_model_name'])


    t = ThreadHandler(target=partial(haar_cascade), args=[]
                       name="video-haar_cascade")
    t.start()
    #Initialize neural networks, haar cascade, other stuff
    pass

def load_colors(filename):
    colors = {}
    colors_file = open(filename + '.txt', 'r')
    lines = colors_file.readlines()
    for line in lines:
        line = line.strip()
        split = line.split(":")
        color = split[0].strip()
        hex = split[1].strip()
        r = int(hex,16)
        g = int(hex,16)
        b = int(hex,16)
        colors[color] = [r,g,b]
    return colors

def load_model(model_name):
    # load json and create model
    json_file = open(model_name+'.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    model = model_from_json(loaded_model_json)
    # load weights into new model
    model.load_weights(model_name+".h5")
    print("Loaded model from " + model_name)
    return model


def haar_cascade():
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
def get_color_name(rgb_triplet):
    minname = ""
    mindiff = float("inf")
    for color in colors_dict:
        rgb = colors_dict[color]
        rd = (rgb[0] - rgb_triplet[0]) ** 2
        gd = (rgb[1] - rgb_triplet[1]) ** 2
        bd = (rgb[2] - rgb_triplet[2]) ** 2
        if rd + gd + bd < mindiff:
            mindiff = rd + gd + bd
            minname = color
    return minname

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
