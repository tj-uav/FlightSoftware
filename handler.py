from telemetry import Telemetry

class Handler:

    def __init__(self, config):
        self.config = config
        self.telemetry = Telemetry(config)

    
    def run(self):
        # This is the main while loop that does all the control stuff
        while True:
            raise NotImplementedError
