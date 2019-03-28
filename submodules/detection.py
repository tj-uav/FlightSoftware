import cv2


#List of objects currently being detected
active_objects = []

def start():
    #Initialize neural networks, haar cascade, other stuff
    pass

def haar_cascade(image):
    #If ROI detected:
    t = ThreadHandler(target=partial(process_image), args=[image,object_image]
                       name="detection-process_image")
    t.start()
    #else:
    pass

def process_image(original_img, object_img):
    """
    This method is called when the haar cascade detects an ROI suspicious of being an object
    """
    (shape_color,alpha_color) = get_colors(object_image)
    shape = classify_shape(object_img, shape_color)
    alpha = classify_alpha(object_img, alpha_color)
    (latitude,longitude) = get_position()
    dict = {"shape":shape, "alpha":alpha, "latitude":latitude, "longitude":longitude}
    pass

def classify_shape(object_img, color):
    pass

def classify_alpha(object_img, color):
    pass

def gps_data():
    pass

def get_position(image, center):
    global altitude, camera_angle
    (latitude, longitude) = gps_data()
    #Do some quick maths
    return (object_latitude, object_longitude)

def make_json():
    pass
