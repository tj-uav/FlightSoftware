import sys, socket
from PIL import Image
import io

# Both of these are your computer's local IP - we use this for testing
# On a Wi-Fi network, you can find your IP with ipconfig (Windows) or ifconfig (Mac/Linux) in terminal
MY_IP = '127.0.0.1'
OTHER_IP = '127.0.0.1'
PORT = 5005 # Arbitrary

def send(filepath):
    global MY_IP, OTHER_IP, PORT

    img = Image.open(filepath)
    byte_obj = io.BytesIO()
    img.save(byte_obj, format=img.format)
    byte_obj.seek(0)
    byte_array = byte_obj.read()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((OTHER_IP, PORT))
    print("Sending data...")
    sock.send(byte_array)
    print("Done")

    sock.close()


def receive():
    global MY_IP, PORT
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((MY_IP, PORT))
    sock.listen(1)
    conn, addr = sock.accept()

    img_data = b''
    while True:
        received = conn.recv(1024)
        if img_data and not received: break
        img_data += received

    print("Received image")
    print(img_data)
    byte_obj = io.BytesIO(img_data)

    img = Image.open(byte_obj)
    img.show()

    conn.close()
    sock.close()

# Parse command-line inputs (if there are any)
filepath = ''
role = ''
for arg in sys.argv:
    if '.jpg' in arg or '.png' in arg: # If the argument looks like an image filepath
        filepath = arg
    
    if arg == 'send' or arg == 'receive':
        role = arg

# If no role given, prompt user
if not role: role = input('Role (send or receive): ').lower()
# If the script is sending an image, it needs the filepath
if role == 'send' and filepath=='': 
    filepath = input("filepath: ")


if role == 'send':
    send(filepath)
elif role == 'receive':
    receive()
else:
    print("invalid role given")