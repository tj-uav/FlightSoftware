import cv2, io, socket, struct, time, os, sys
import pickle, zlib, base64, numpy
from PIL import Image
from io import BytesIO


MY_IP = '127.0.0.1'
OTHER_IP = '127.0.0.1'
PORT = 5005 # Arbitrary
quality = 35

def compress(frame):
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	img = Image.fromarray(frame)
	byte_obj = io.BytesIO()
	#print(byte_obj)
	img.save(byte_obj, format='JPEG', quality=quality)
	byte_obj.seek(0)
	byte_array = byte_obj.read()
	return byte_array

def send(cameraVal):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((OTHER_IP, PORT))

	#connection = sock.makefile('wb')

	cam = cv2.VideoCapture(cameraVal)

	# cam.set(3, 320)
	# cam.set(4, 240)

	img_counter = 0

	#encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

	while True:
		ret, frame = cam.read()
		if ret:
			byte_array = compress(frame)				
			sock.send(byte_array)

	cam.release()

def receive():
    global MY_IP, PORT
    if not os.path.exists('imageStream'):
        os.makedirs('imageStream')

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((MY_IP, PORT))
    sock.listen(1)
    conn, addr = sock.accept()

    imageCounter=0

    while True:
        img_data = b''
        imageCounter += 1
        # b = True
        # while b:
        #     received = conn.recv(1024)
        #     if img_data and received == b'':
        #         break 
        #         b=False
        #     else:
        #         img_data += received
        #         print(received)
        received = conn.recv(9999999)
        if received:
            img_data += received
            print("Received image")
            #print(img_data)
            byte_obj = io.BytesIO(img_data)

            img = Image.open(byte_obj)
            img.save('imageStream/' + str(imageCounter)+'.jpg', format='JPEG')
            #img.show()
            print(imageCounter)
        else:
            break
    
    print("Finished")
    conn.close()
    sock.close()


    # global MY_IP, OTHER_IP, PORT

    # img = Image.open(filepath)
    # byte_obj = io.BytesIO()
    # img.save(byte_obj, format=img.format, quality=35)
    # print(img.format)
    # byte_obj.seek(0)
    # byte_array = byte_obj.read()

    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.connect((OTHER_IP, PORT))
    # print("Sending data...")
    # sock.send(byte_array)
    # print("Done")

    # sock.close()

role = ''
for arg in sys.argv:
    if arg == 'send' or arg == 'receive':
        role = arg

# If no role given, prompt user
if not role: role = input('Role (send or receive): ').lower()
# If the script is sending an image, it needs the filepath

if role == 'send':
	send(0)
elif role == 'receive':
	receive()
else:
	print("invalid role given")
