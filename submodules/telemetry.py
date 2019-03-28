# TODO: Uses placeholder variables in other files, so make it use actual values
# TODO: what if radio turned off during a burst?
from Crypto.Cipher import AES
import socket
import logging
import time
from functools import partial
from threading import Lock

from core import config
from helpers.threadhandler import ThreadHandler
from .command_ingest import command

logger = logging.getLogger("TELEMETRY")
BUFFER_SIZE = 1024 #Defualt/Starting buffer size

def telemetry_send():
    """
    Thread method to burst the telemetry every so often
    """
    # TODO: check battery levels before sending
    global packet_queue, sock_send

    while True:
        if len(packet_queue > 0):
            (send_message,send_buffer) = packet_queue.popleft()
            if send_buffer > curr_buffer:
                logger.debug("Setting ground station buffer to " + str(send_buffer))
                sock_send.send("SET_BUFFER" + str(send_buffer))
                time.sleep(config['telemetry']['send_interval'])
            sock_send.send(send_message)
            logger.debug("Sent message to ground station")
            time.sleep(config['telemetry']['send_interval'])

def telemetry_receive():
    """
    Constantly looking for data from ground station to receive, sends message to command_ingest once received
    """
    global conn
    while True:
        data = conn.recv(BUFFER_SIZE)
        logger.debug("Received data from ground station")
        plaintext = decrypt(data)
        plaintext = data.decode("utf-8")
        ingest_message(plaintext)
        time.sleep(config['telemetry']['receive_interval'])

def enqueue(message):
    """
    Enqueue an event message.
    :param message: message to enqueue.
    """
    global packet_queue
    ciphertext = message.encode("utf-8")
    ciphertext = encrypt(message)
    buffer = len(ciphertext)
    packet_queue.append((ciphertext,buffer))
    logger.debug("Added message to queue")

def encrypt(plaintext): #Need to add padding (PKCS1_OAEP)
    global key
    encrypt_cipher = AES.new(key, AES.MODE_EAX)
    ciphertext = encrypt_cipher.encrypt(plaintext)
    return ciphertext

def decrypt(ciphertext): #Need to add padding (PKCS1_OAEP)
    global key
    decrypt_cipher = AES.new(key, AES.MODE_EAX, cipher.nonce)
    plaintext = decrypt_cipher.decrypt(ciphertext)
    return plaintext

@command("clear")
def clear_buffers():
    global packet_lock, event_packet_buffer, telem_packet_buffer
    with packet_lock:
        event_packet_buffer.clear()
        telem_packet_buffer.clear()

def start():
    """
    Starts the telemetry send thread
    """

    global packet_queue, sock_send, sock_receive, conn
    global key
    key = get_random_bytes(16)
    ground_ip = config['telemetry']['ground_ip']
    port = config['telemetry']['port']
    packet_queue = collections.deque([]) #Might wanna use priority queue instead

    #Initialize sending sockets - Do we need separate sockets for sending and receiving?
    sock_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_send.connect((ground_ip,port))

    sock_receive = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_receive.bind(())
    sock_receive.listen(1)
    conn, addr = sock_receive.accept()

    t1 = ThreadHandler(target=partial(telemetry_send),
                       name="telemetry-telemetry_send")
    t1.start()
    t2 = ThreadHandler(target=partial(telemetry_receive),
                       name="telemetry-telemetry_receive")
    t2.start()
