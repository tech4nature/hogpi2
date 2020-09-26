import serial
from datetime import datetime
import re
import json
from json_minify import json_minify
from logging import getLogger
from pathlib import Path
from typing import Dict

logger = getLogger("tunnel.rfid")
config: Dict = json.loads(json_minify(
    open(Path.home() / 'data' / 'config.json', 'r+').read()))['rfid']

# docs: http://www.priority1design.com.au/rfidrw-e-ttl.pdf


class sensor:
    def __init__(self):
        self.ser = serial.Serial(
            port="/dev/ttyAMA0",
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=config['rfid_timeout'],
        )

        if config["rfid_tag_type"] == "EM4100":
            self.matcher = re.compile("[0-9A-F]{10}")
            self.tag_size = 10
            self.ser.write(b'sd0\r\n')
        elif config["rfid_tag_type"] == "FDX-B":
            self.matcher = re.compile("[0-9]{3}_[0-9]{12}")
            self.tag_size = 16
            self.ser.write(b'sd2\r\n')

        self.ser.write(b'sl4\r\n')
        self.ser.read_until(size=6)

    def read(self):
        self.ser.reset_input_buffer()  # clean buffer
        self.ser.reset_output_buffer()  # clean buffer

        raw_tag = self.ser.read_until(size=self.tag_size + 1)
        # byte count = self.tag_size + \r = self.tag_size + 1

        try:
            logger.debug(f"Raw RFID data is: {raw_tag}")
            tag = self.matcher.findall(raw_tag.decode())[0]  # Decode uses the UTF-8 codec
            return tag
        except Exception as e:
            logger.error(e)
            return "TagNotPresent"
