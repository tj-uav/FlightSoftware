import numpy as np

class Packet:

    def __init__(self, header: str, data: dict):
        self.header = header
        self.data = data


    def to_string(self) -> bytes:
        # Example data: {'img': cv2 image, 'geo_data': dict of geo data}
        # Another example data: {'command_header': 'UGV_DROP', 'confirmation': True}
        raise NotImplementedError


    def from_string(self, packet_bytes: bytes) -> Packet:
        raise NotImplementedError

