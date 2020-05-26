import time
import socket
from collections import deque
from threading import Thread

from packet import Packet

# TODO: Use try catch to avoid any errors
# TODO: Reset the socket connection if it breaks

class Telemetry:

    def __init__(self, config):
        self.config = config
        self.send_delay = config["SEND_DELAY"]
        self.create_socket()
        self.ingest_queue = deque([])
        self.buffer = 1024
        self.recv_thread = Thread(target=self.recv_loop)
        self.recv_loop.daemon = True
        self.recv_loop.start()
        self.last_send_time = None


    def create_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.config["GS_IP"], self.config["GS_PORT"]))


    def send_packet(self, packet: Packet):
        # Wait for some time before sending another packet, don't spam since that could cause problems
        while self.last_send_time and self.last_send_time - time.time() < self.send_delay:
            pass
        packet_bytes = packet.to_string()
        # Send packet
        self.sock.send(packet_bytes)
        self.last_send_time = time.time()


    def recv_loop(self):
        while True:
            # Receive data and convert it to a packet
            data = self.sock.recv(self.buffer)
            data = data.decode()
            packet = Packet.from_string(data)
            # Add that packet to a queue of packets that is ready to be ingested by the main class
            self.ingest_queue.append(packet)
