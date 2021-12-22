import json
import socket

with open("config.json", "r") as file:
    config = json.load(file)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((config["conn"]["host"], config["conn"]["port"]))
        # Spaces mark the end of the message, and therefore cannot be included in the base64 string
        img = "image base64 here"
        img = img.replace(" ", "")
        send = bytes(img, "utf-8") + b" "
        s.sendall(send)
        while True:
            resp = s.recv(1024)
            if not resp:
                break

except ConnectionRefusedError as e:
    print(str(e))
