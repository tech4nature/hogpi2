import serial
import time

timeout = 1
global TagFound
global tag
TagFound = None
tag = None

# docs: http://www.priority1design.com.au/rfidrw-e-ttl.pdf


class sensor:
    def __init__(self, rfid_record_time):
        global ser
        ser = serial.Serial(
            port="/dev/ttyAMA0",
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=rfid_record_time,
        )

    def read(self):
        ser.reset_input_buffer()  #  clean buffer
        ser.reset_output_buffer()  # clean buffer
        ser.write(b"sd2\r\n")  # set mode of rfid
        a = ser.read_until(size=19).decode(
            "utf-8"
        )  # 16 byte  + \r + \n somehow is 19 not 18
        if len(a) > 15:  # if read then return out of function
            return a  # return and break out of functions
        return "TagNotPresent"  # return only if timed out
