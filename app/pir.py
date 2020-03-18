# from RPi import GPIO
from RPi import GPIO
import time
import logging


logger = logging.getLogger(__name__)


class sensor:
    def __init__(self, pin_num):
        self.pin = pin_num
        time.sleep(2)  # set up of PIR reader
        GPIO.setmode(GPIO.BCM)  # set mode
        GPIO.setup(
            self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN
        )  # Set the PIR to pin 8

    def read(self, iterations=300):
        # logger.debug("Read value %s from pin %s", RPi.GPIO.input(pin), pin)
        value = 0
        for _ in range(iterations):  # sample iteration times
            if GPIO.input(self.pin) == 1:  # count the positive reads
                value = value + 1
                # print(value)  # leave in for commissioning
                # print(iterations)  # leave in for commissioning
        if value == iterations:  # if all positive then return 1
            return True
        else:
            return False
