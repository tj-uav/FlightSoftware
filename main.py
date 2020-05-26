import json
from handler import Handler

config = json.load(open("config.json"))
handler = Handler(config)
handler.run()