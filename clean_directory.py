import os

images = os.path.join(os.getcwd() + "/images")

for direc in [images]:
    for file in os.listdir(direc):
        if file != "sample.png":
            os.remove(os.path.join(direc, file))
