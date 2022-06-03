import os

images = os.path.join(os.getcwd() + "/assets/images")

for direc in [images]:
    for file in os.listdir(direc):
        if file != "sample.png":
            os.remove(os.path.join(direc, file))

# Clear log files
for log_file in ("nohup.out", "fs.log"):
    if os.path.isfile(log_file):
        open(log_file, "w", encoding="utf-8").close()
