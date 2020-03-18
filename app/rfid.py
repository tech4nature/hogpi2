import serial
import time
from logging import getLogger

logger = getLogger(__name__)

# docs: http://www.priority1design.com.au/rfidrw-e-ttl.pdf

class sensor:
    def __init__(self, rfid_record_time):
        self.ser = serial.Serial(
            port="/dev/ttyAMA0",
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=rfid_record_time,
        )

    def read(self):
        logger.info("Reading RFID")
        self.ser.reset_input_buffer()  # clean buffer
        self.ser.reset_output_buffer()  # clean buffer
        self.ser.write(b"sd2\r\n")  # set mode of rfid
        tag = self.ser.read_until(size=19).decode()  # 16 byte  + \r + \n somehow is 19 not 18
        
        logger.debug(f"Got: {tag}")
        if len(tag) > 15:  # if read then return out of function
            logger.info(f"Found tag: {tag}")
            return tag  # return and break out of functions

        logger.info("Tag not present")
        return "TagNotPresent"  # return only if timed out
